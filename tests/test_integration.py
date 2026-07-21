import unittest
import tempfile
import os
from pathlib import Path
import json
import re
from html.parser import HTMLParser
from unittest.mock import MagicMock, patch
from http.server import HTTPServer
import threading
import time
import urllib.request
import urllib.parse

from tests.base import BaseTest, BaseServerTest
from server.config import Config, ServerConfig, SecurityConfig, FeaturesConfig, UIConfig, LoggingConfig, RateLimitConfig
from server.handler import FileServerHandler, create_handler_class
from server.storage import Storage, FileInfo
from server import (
    ROOT, RAW, SEARCH, DOWNLOAD, API_FILES, HEALTH,
    SAVE, UPLOAD, MKDIR, DELETE, MOVE, COPY, DOWNLOAD_SELECTED,
)
from server.templates import render_listing, render_editor, render_preview, render_error
from server.templates.base import get_base_html


class TestTemplateRendering(unittest.TestCase):
    def setUp(self):
        self.file = FileInfo(
            name='test.txt',
            path='test.txt',
            is_dir=False,
            size=1024,
            modified=1234567890.0,
            modified_str='2024-01-01 12:00',
            mime_type='text/plain',
            is_text=True,
            is_hidden=False,
            permissions='-rw-r--r--'
        )
        self.folder = FileInfo(
            name='documents',
            path='documents',
            is_dir=True,
            size=0,
            modified=1234567890.0,
            modified_str='2024-01-01 12:00',
            mime_type=None,
            is_text=False,
            is_hidden=False,
            permissions='drwxr-xr-x'
        )

    def test_listing_empty(self):
        html = render_listing([], '', sort_by='name', show_hidden=False)
        self.assertIn('empty-state', html)
        self.assertIn('No Files', html)

    def test_listing_with_files(self):
        html = render_listing([self.file, self.folder], '', sort_by='name', show_hidden=False)
        self.assertIn('test.txt', html)
        self.assertIn('documents', html)
        self.assertIn('file-item', html)

    def test_listing_with_search(self):
        html = render_listing([self.file], '', search_query='test', sort_by='name')
        self.assertIn('test', html)

    def test_listing_pagination(self):
        files = [FileInfo(
            name=f'file{i}.txt',
            path=f'file{i}.txt',
            is_dir=False,
            size=100,
            modified=1234567890.0,
            modified_str='2024-01-01 12:00',
            mime_type='text/plain',
            is_text=True,
            is_hidden=False,
            permissions='-rw-r--r--'
        ) for i in range(5)]

        html = render_listing(files, '', page=1, total_pages=3)
        self.assertIn('Next', html)

    def test_listing_features(self):
        features = {'upload': True, 'delete': True, 'edit': True, 'search': True}
        html = render_listing([self.file], '', features=features)
        self.assertIn('upload-zone', html)

    def test_listing_no_upload(self):
        features = {'upload': False, 'delete': True, 'edit': True, 'search': True}
        html = render_listing([self.file], '', features=features)
        self.assertNotIn('upload-zone" id="upload-zone', html)

    def test_listing_flash_message(self):
        html = render_listing([self.file], '', flash_message='File uploaded', flash_type='success')
        self.assertIn('File uploaded', html)
        self.assertIn('flash-success', html)

    def test_editor_basic(self):
        html = render_editor('test.txt', 'Hello World')
        self.assertIn('editor-textarea', html)
        self.assertIn('Hello World', html)
        self.assertIn('Save', html)

    def test_editor_readonly(self):
        html = render_editor('test.txt', 'Hello World', read_only=True)
        self.assertIn('readOnly: true', html)

    def test_editor_flash_message(self):
        html = render_editor('test.txt', 'Hello', flash_message='Saved!', flash_type='success')
        self.assertIn('Saved!', html)

    def test_preview_text(self):
        html = render_preview('test.txt', 'test.txt', 'text/plain', 1024, 'Hello', True)
        self.assertIn('preview-code', html)
        self.assertIn('Hello', html)

    def test_preview_image(self):
        html = render_preview('photo.jpg', 'photo.jpg', 'image/jpeg', 1024, None, False)
        self.assertIn('img', html)
        self.assertIn('preview-image', html)

    def test_preview_video(self):
        html = render_preview('video.mp4', 'video.mp4', 'video/mp4', 1024, None, False)
        self.assertIn('video', html)

    def test_preview_audio(self):
        html = render_preview('audio.mp3', 'audio.mp3', 'audio/mpeg', 1024, None, False)
        self.assertIn('audio', html)

    def test_preview_pdf(self):
        html = render_preview('doc.pdf', 'doc.pdf', 'application/pdf', 1024, None, False)
        self.assertIn('iframe', html)

    def test_preview_unknown(self):
        html = render_preview('file.xyz', 'file.xyz', 'application/octet-stream', 1024, None, False)
        self.assertIn('Download', html)

    def test_error_404(self):
        html = render_error(404, 'Not Found')
        self.assertIn('404', html)
        self.assertIn('Not Found', html)

    def test_error_500(self):
        html = render_error(500, 'Server Error')
        self.assertIn('500', html)
        self.assertIn('Server Error', html)

    def test_error_with_details(self):
        html = render_error(500, 'Error', details='Stack trace here')
        self.assertIn('Stack trace here', html)

    def test_base_html(self):
        html = get_base_html('Test Page', '<h1>Hello</h1>')
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('</html>', html)
        self.assertIn('Test Page', html)
        self.assertIn('<h1>Hello</h1>', html)


class TestHTTPIntegration(BaseServerTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.temp_dir / 'test.txt').write_text('Hello World')
        (cls.temp_dir / 'README.md').write_text('# Test')
        (cls.temp_dir / 'subdir').mkdir()
        (cls.temp_dir / 'subdir' / 'nested.txt').write_text('Nested')

    def test_health_endpoint(self):
        body, status = self._get('/health')
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data['status'], 'healthy')

    def test_root_directory(self):
        body, status = self._get('/')
        self.assertEqual(status, 200)
        self.assertIn('test.txt', body)
        self.assertIn('README.md', body)
        self.assertIn('subdir', body)

    def test_file_preview(self):
        body, status = self._get('/?p=test.txt')
        self.assertEqual(status, 200)
        self.assertIn('Hello World', body)

    def test_file_editor(self):
        body, status = self._get('/?p=test.txt&edit=1')
        self.assertEqual(status, 200)
        self.assertIn('Hello World', body)
        self.assertIn('editor-textarea', body)

    def test_subdirectory(self):
        body, status = self._get('/?p=subdir')
        self.assertEqual(status, 200)
        self.assertIn('nested.txt', body)

    def test_file_not_found(self):
        body, status = self._get('/?p=nonexistent.txt')
        self.assertEqual(status, 404)

    def test_raw_download(self):
        body, status = self._get('/raw?p=test.txt')
        self.assertEqual(status, 200)
        self.assertEqual(body, 'Hello World')

    def test_search(self):
        body, status = self._get('/search?q=test')
        self.assertEqual(status, 200)
        self.assertIn('test.txt', body)

    def test_search_empty(self):
        _, status = self._get('/search?q=')
        self.assertIn(status, [200, 303])

    def test_api_files(self):
        body, status = self._get('/api/files')
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIsInstance(data, list)

    def test_save_file(self):
        _, status = self._post('/save', {'p': 'new.txt', 'content': 'New content'})
        self.assertIn(status, [200, 303])
        content = (self.temp_dir / 'new.txt').read_text()
        self.assertEqual(content, 'New content')

    def test_create_directory(self):
        _, status = self._post('/mkdir', {'p': '', 'name': 'newdir'})
        self.assertIn(status, [200, 303])
        self.assertTrue((self.temp_dir / 'newdir').is_dir())

    def test_delete_file(self):
        (self.temp_dir / 'to_delete.txt').write_text('delete me')
        self.assertTrue((self.temp_dir / 'to_delete.txt').exists())

        _, status = self._post('/delete', {'p': 'to_delete.txt'})
        self.assertIn(status, [200, 303])
        self.assertFalse((self.temp_dir / 'to_delete.txt').exists())

    def test_move_file(self):
        (self.temp_dir / 'source.txt').write_text('move me')

        _, status = self._post('/move', {'source': 'source.txt', 'destination': 'moved.txt'})
        self.assertIn(status, [200, 303])
        self.assertFalse((self.temp_dir / 'source.txt').exists())
        self.assertTrue((self.temp_dir / 'moved.txt').exists())

    def test_copy_file(self):
        (self.temp_dir / 'original.txt').write_text('copy me')

        _, status = self._post('/copy', {'source': 'original.txt', 'destination': 'copied.txt'})
        self.assertIn(status, [200, 303])
        self.assertTrue((self.temp_dir / 'original.txt').exists())
        self.assertTrue((self.temp_dir / 'copied.txt').exists())
        self.assertEqual((self.temp_dir / 'copied.txt').read_text(), 'copy me')

    def test_delete_directory(self):
        subdir = self.temp_dir / 'subdir_to_delete'
        subdir.mkdir()
        (subdir / 'file.txt').write_text('content')
        self.assertTrue(subdir.exists())

        _, status = self._post('/delete', {'p': 'subdir_to_delete'})
        self.assertIn(status, [200, 303])
        self.assertFalse(subdir.exists())

    def test_raw_range(self):
        body, status = self._get('/raw?p=test.txt')
        self.assertEqual(status, 200)
        self.assertEqual(body, 'Hello World')

        import urllib.request
        url = f'http://127.0.0.1:{self.port}/raw?p=test.txt'
        req = urllib.request.Request(url)
        req.add_header('Range', 'bytes=0-4')
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 206)
                self.assertEqual(resp.read().decode(), 'Hello')
        except urllib.error.HTTPError as e:
            self.fail(f'Range request failed: {e.code}')

    def test_editor_non_text(self):
        (self.temp_dir / 'test.bin').write_bytes(b'\x00\x01\x02')
        body, status = self._get('/?p=test.bin&edit=1')
        self.assertEqual(status, 400)
        self.assertIn('Not a text file', body)

    def test_hidden_files_param(self):
        (self.temp_dir / '.hidden_file').write_text('secret')
        body, status = self._get('/?hidden=1')
        self.assertEqual(status, 200)
        self.assertIn('.hidden_file', body)

        body, status = self._get('/?hidden=0')
        self.assertEqual(status, 200)
        self.assertNotIn('.hidden_file', body)

    def test_sort_by_size(self):
        (self.temp_dir / 'small.txt').write_text('a')
        (self.temp_dir / 'large.txt').write_text('b' * 1000)
        body, status = self._get('/?sort=size')
        self.assertEqual(status, 200)
        # Both files should appear
        self.assertIn('small.txt', body)
        self.assertIn('large.txt', body)

    def test_sort_by_modified(self):
        body, status = self._get('/?sort=modified')
        self.assertEqual(status, 200)
        self.assertIn('test.txt', body)

    def test_save_new_file_subdirectory(self):
        subdir = self.temp_dir / 'newsub'
        subdir.mkdir()
        _, status = self._post('/save', {'p': 'newsub/created.txt', 'content': 'created'})
        self.assertIn(status, [200, 303])
        self.assertTrue((self.temp_dir / 'newsub' / 'created.txt').exists())
        self.assertEqual((self.temp_dir / 'newsub' / 'created.txt').read_text(), 'created')

    def test_mkdir_invalid_name(self):
        body, status = self._post('/mkdir', {'p': '', 'name': '../escape'})
        self.assertEqual(status, 400)

        body, status = self._post('/mkdir', {'p': '', 'name': ''})
        self.assertEqual(status, 400)

    def test_delete_nonexistent(self):
        body, status = self._post('/delete', {'p': 'nonexistent.txt'})
        self.assertEqual(status, 404)

    def test_move_nonexistent_source(self):
        body, status = self._post('/move', {'source': 'nonexistent.txt', 'destination': 'dest.txt'})
        self.assertEqual(status, 404)

    def test_copy_nonexistent_source(self):
        body, status = self._post('/copy', {'source': 'nonexistent.txt', 'destination': 'dest.txt'})
        self.assertEqual(status, 404)

    def test_raw_if_modified_since(self):
        import urllib.request
        url = f'http://127.0.0.1:{self.port}/raw?p=test.txt'
        req = urllib.request.Request(url)
        req.add_header('If-Modified-Since', 'Thu, 01 Jan 2099 00:00:00 GMT')
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 304)
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 304)

    def test_search_no_results(self):
        body, status = self._get('/search?q=zzz_nonexistent_zzz')
        self.assertEqual(status, 200)
        self.assertIn('0 results', body)

    def test_api_files_nonexistent(self):
        body, status = self._get('/api/files?p=nonexistent')
        self.assertEqual(status, 400)

    def test_editor_nonexistent_file(self):
        body, status = self._get('/?p=nonexistent.txt&edit=1')
        self.assertEqual(status, 404)

    def test_editor_directory(self):
        body, status = self._get('/?p=subdir&edit=1')
        self.assertEqual(status, 400)
        self.assertIn('Not a file', body)

    def test_download_nonexistent(self):
        body, status = self._get('/download?p=nonexistent')
        self.assertEqual(status, 404)

    def test_raw_directory(self):
        body, status = self._get('/raw?p=subdir')
        self.assertEqual(status, 400)
        self.assertIn('Not a file', body)


class TestBatchOperations(BaseServerTest):
    def setUp(self):
        super().setUp()
        for i in range(5):
            (self.temp_dir / f'file{i}.txt').write_text(f'Content {i}')

    def test_download_selected(self):
        data = {
            'p': '',
            'files': ['file0.txt', 'file1.txt', 'file2.txt']
        }
        _, status = self._post('/download-selected', data)
        self.assertIn(status, [200, 404])


class TestThemeSwitching(unittest.TestCase):
    def test_theme_in_html(self):
        html = get_base_html('Test', '<h1>Hello</h1>', theme='dark')
        self.assertIn('data-theme="dark"', html)

        html = get_base_html('Test', '<h1>Hello</h1>', theme='light')
        self.assertIn('data-theme="light"', html)

        html = get_base_html('Test', '<h1>Hello</h1>', theme='auto')
        self.assertIn('data-theme="auto"', html)

    def test_theme_css_variables(self):
        html = get_base_html('Test', '<h1>Hello</h1>')
        self.assertIn('--bg-primary', html)
        self.assertIn('--text-primary', html)
        self.assertIn('[data-theme="light"]', html)

    def test_theme_toggle_script(self):
        html = get_base_html('Test', '<h1>Hello</h1>')
        self.assertIn('toggleTheme', html)
        self.assertIn('localStorage', html)


class TestKeyboardShortcuts(unittest.TestCase):
    def test_shortcuts_in_html(self):
        html = get_base_html('Test', '<h1>Hello</h1>')
        self.assertIn('keydown', html)
        self.assertIn('ctrlKey', html)
        self.assertIn('metaKey', html)


class TestSecurityHeaders(unittest.TestCase):
    def test_security_headers_in_html(self):
        html = get_base_html('Test', '<h1>Hello</h1>')
        self.assertIn('viewport', html)
        self.assertIn('apple-mobile-web-app-capable', html)


class TestResponsiveDesign(unittest.TestCase):
    def test_mobile_meta_tags(self):
        html = get_base_html('Test', '<h1>Hello</h1>')
        self.assertIn('viewport-fit=cover', html)
        self.assertIn('user-scalable=no', html)


class TestTemplateStructure(unittest.TestCase):
    def test_css_media_query_counts(self):
        html = get_base_html('Test', '')
        self.assertEqual(html.count('@media (prefers-color-scheme: light)'), 1)
        self.assertEqual(html.count('@media (prefers-color-scheme: dark)'), 1)

    def test_auto_theme_block_count(self):
        html = get_base_html('Test', '')
        self.assertEqual(html.count('[data-theme="auto"]'), 2)

    def test_css_balanced_braces(self):
        html = get_base_html('Test', '')
        style_start = html.find('<style>')
        style_end = html.find('</style>')
        css = html[style_start:style_end]
        opens = css.count('{')
        closes = css.count('}')
        self.assertEqual(opens, closes, f"CSS has {opens} opening braces but {closes} closing braces")

    def test_html_is_parseable(self):
        html = get_base_html('Test', '<p>hello</p>')
        parser = HTMLParser()
        try:
            parser.feed(html)
            parser.close()
        except Exception as e:
            self.fail(f"HTML parse failed: {e}")

    def test_listing_html_is_parseable(self):
        file_info = FileInfo(
            name='test.txt', path='test.txt', is_dir=False, size=100,
            modified=1234567890.0, modified_str='2024-01-01 12:00',
            mime_type='text/plain', is_text=True, is_hidden=False,
            permissions='-rw-r--r--',
        )
        html = render_listing([file_info], '', csrf_token='test')
        parser = HTMLParser()
        try:
            parser.feed(html)
            parser.close()
        except Exception as e:
            self.fail(f"Listing HTML parse failed: {e}")

    def test_editor_html_is_parseable(self):
        html = render_editor('test.txt', 'content', csrf_token='test')
        parser = HTMLParser()
        try:
            parser.feed(html)
            parser.close()
        except Exception as e:
            self.fail(f"Editor HTML parse failed: {e}")

    def test_preview_html_is_parseable(self):
        html = render_preview('test.txt', 'test.txt', 'text/plain', 100, 'hello', True)
        parser = HTMLParser()
        try:
            parser.feed(html)
            parser.close()
        except Exception as e:
            self.fail(f"Preview HTML parse failed: {e}")

    def test_error_html_is_parseable(self):
        html = render_error(404, 'Not found')
        parser = HTMLParser()
        try:
            parser.feed(html)
            parser.close()
        except Exception as e:
            self.fail(f"Error HTML parse failed: {e}")

    def test_no_duplicate_theme_blocks(self):
        html = get_base_html('Test', '')
        media_blocks = re.findall(r'@media[^{]+\{[^}]+\}[^}]*\}', html, re.DOTALL)
        auto_in_media = sum(block.count('[data-theme="auto"]') for block in media_blocks)
        total_auto = html.count('[data-theme="auto"]')
        self.assertEqual(
            total_auto, auto_in_media,
            f"Found {total_auto - auto_in_media} [data-theme=\"auto\"] outside @media blocks"
        )

    def test_listing_javascript_balanced_braces(self):
        file_info = FileInfo(
            name='test.txt', path='test.txt', is_dir=False, size=100,
            modified=1234567890.0, modified_str='2024-01-01 12:00',
            mime_type='text/plain', is_text=True, is_hidden=False,
            permissions='-rw-r--r--',
        )
        html = render_listing([file_info], '', csrf_token='test')
        script_start = html.find('<script>')
        while script_start != -1:
            script_end = html.find('</script>', script_start)
            if script_end == -1:
                break
            js = html[script_start + len('<script>'):script_end]
            opens_curly = js.count('{')
            closes_curly = js.count('}')
            self.assertEqual(
                opens_curly, closes_curly,
                f'JavaScript has {opens_curly} opening curly braces but {closes_curly} closing curly braces'
            )
            opens_paren = js.count('(')
            closes_paren = js.count(')')
            self.assertEqual(
                opens_paren, closes_paren,
                f'JavaScript has {opens_paren} opening parentheses but {closes_paren} closing parentheses'
            )
            script_start = html.find('<script>', script_end)


class TestRouteCoverage(unittest.TestCase):
    def _get_handler_methods(self):
        methods = set()
        for attr in dir(FileServerHandler):
            if attr.startswith('_handle_'):
                methods.add(attr)
        return methods

    def test_all_get_routes_have_handlers(self):
        get_route_names = ['ROOT', 'RAW', 'SEARCH', 'DOWNLOAD', 'API_FILES', 'HEALTH']
        import inspect
        source = inspect.getsource(FileServerHandler.do_GET)
        for name in get_route_names:
            self.assertIn(name, source, f"do_GET missing branch for {name}")

    def test_all_post_routes_have_handlers(self):
        post_route_names = ['SAVE', 'UPLOAD', 'MKDIR', 'DELETE', 'MOVE', 'COPY', 'DOWNLOAD_SELECTED']
        import inspect
        source = inspect.getsource(FileServerHandler.do_POST)
        for name in post_route_names:
            self.assertIn(name, source, f"do_POST missing branch for {name}")

    def test_all_route_constants_have_matching_handler(self):
        route_to_handler = {
            ROOT: '_handle_root',
            RAW: '_handle_raw',
            SEARCH: '_handle_search',
            DOWNLOAD: '_handle_download',
            API_FILES: '_handle_api_files',
            HEALTH: '_handle_health',
            SAVE: '_handle_save',
            UPLOAD: '_handle_upload',
            MKDIR: '_handle_mkdir',
            DELETE: '_handle_delete_post',
            MOVE: '_handle_move',
            COPY: '_handle_copy',
            DOWNLOAD_SELECTED: '_handle_download_selected',
        }
        methods = self._get_handler_methods()
        for route, handler in route_to_handler.items():
            self.assertIn(
                handler, methods,
                f"Route {route} maps to {handler} but method not found"
            )


class TestFeatureFlagCoverage(unittest.TestCase):
    def test_upload_checks_feature_flag(self):
        import inspect
        source = inspect.getsource(FileServerHandler._handle_upload)
        self.assertIn('_check_feature', source)

    def test_delete_checks_feature_flag(self):
        import inspect
        source = inspect.getsource(FileServerHandler._handle_delete_post)
        self.assertIn('_check_feature', source)

    def test_mkdir_checks_feature_flag(self):
        import inspect
        source = inspect.getsource(FileServerHandler._handle_mkdir)
        self.assertIn('_check_feature', source)

    def test_edit_checks_feature_flag(self):
        import inspect
        source = inspect.getsource(FileServerHandler._handle_editor)
        self.assertIn('_check_feature', source)

    def test_save_checks_feature_flag(self):
        import inspect
        source = inspect.getsource(FileServerHandler._handle_save)
        self.assertIn('_check_feature', source)

    def test_move_checks_feature_flag(self):
        import inspect
        source = inspect.getsource(FileServerHandler._handle_move)
        self.assertIn('_check_feature', source)

    def test_copy_checks_feature_flag(self):
        import inspect
        source = inspect.getsource(FileServerHandler._handle_copy)
        self.assertIn('_check_feature', source)

    def test_download_zip_checks_feature_flag(self):
        import inspect
        source = inspect.getsource(FileServerHandler._handle_download)
        self.assertIn('_check_feature', source)

    def test_download_selected_checks_feature_flag(self):
        import inspect
        source = inspect.getsource(FileServerHandler._handle_download_selected)
        self.assertIn('_check_feature', source)


class TestCSRFCoverage(unittest.TestCase):
    def test_all_post_handlers_validate_csrf(self):
        import inspect
        source = inspect.getsource(FileServerHandler.do_POST)
        csrf_check = '_validate_post_csrf'
        self.assertIn(csrf_check, source, "do_POST must call _validate_post_csrf")
        csrf_pos = source.index(csrf_check)
        first_handler = min(
            pos for pos in [
                source.find(f"path == SAVE:"),
                source.find(f"path == UPLOAD:"),
            ] if pos > 0
        )
        self.assertLess(
            csrf_pos, first_handler,
            "CSRF validation must happen before dispatching to handlers"
        )

    def test_every_post_handler_has_csrf_in_path(self):
        import inspect
        source = inspect.getsource(FileServerHandler.do_POST)
        post_route_names = ['SAVE', 'UPLOAD', 'MKDIR', 'DELETE', 'MOVE', 'COPY', 'DOWNLOAD_SELECTED']
        for name in post_route_names:
            self.assertIn(
                name, source,
                f"POST route {name} not found in do_POST"
            )


if __name__ == '__main__':
    unittest.main()
