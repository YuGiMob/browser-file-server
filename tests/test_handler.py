import unittest
import os
import json
from pathlib import Path

from tests.base import BaseTest, BaseServerTest
from server.storage import Storage
from server.handler import FileServerHandler


class TestHandlerIntegration(BaseTest):
    def test_directory_listing(self):
        (self.temp_dir / "file1.txt").write_text("content1")
        (self.temp_dir / "file2.txt").write_text("content2")
        (self.temp_dir / "subdir").mkdir()

        storage = self.make_storage()
        files = storage.list_directory(self.temp_dir)
        self.assertEqual(len(files), 3)
        self.assertTrue(files[0].is_dir)
        self.assertEqual(files[0].name, "subdir")

    def test_file_operations(self):
        (self.temp_dir / "test.txt").write_text("Hello")
        self.assertEqual((self.temp_dir / "test.txt").read_text(), "Hello")

        (self.temp_dir / "test.txt").rename(self.temp_dir / "renamed.txt")
        self.assertFalse((self.temp_dir / "test.txt").exists())
        self.assertTrue((self.temp_dir / "renamed.txt").exists())

        (self.temp_dir / "renamed.txt").unlink()
        self.assertFalse((self.temp_dir / "renamed.txt").exists())

    def test_file_search(self):
        (self.temp_dir / "test1.txt").write_text("content1")
        (self.temp_dir / "test2.txt").write_text("content2")
        (self.temp_dir / "other.txt").write_text("content3")

        storage = self.make_storage()
        results = storage.search("test")
        self.assertEqual(len(results), 2)

    def test_file_info(self):
        (self.temp_dir / "test.txt").write_text("Hello, World!")

        storage = self.make_storage()
        info = storage.get_file_info(self.temp_dir / "test.txt")
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "test.txt")
        self.assertFalse(info.is_dir)
        self.assertEqual(info.size, 13)
        self.assertTrue(info.is_text)

    def test_directory_creation(self):
        storage = self.make_storage()
        target = self.temp_dir / "newdir"
        result = storage.create_directory(target)
        self.assertTrue(result)
        self.assertTrue(target.exists())
        self.assertTrue(target.is_dir())

    def test_file_copy(self):
        source = self.temp_dir / "source.txt"
        source.write_text("content")
        dest = self.temp_dir / "dest.txt"

        storage = self.make_storage()
        result = storage.copy(source, dest)
        self.assertTrue(result)
        self.assertTrue(source.exists())
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "content")

    def test_file_move(self):
        source = self.temp_dir / "source.txt"
        source.write_text("content")
        dest = self.temp_dir / "dest.txt"

        storage = self.make_storage()
        result = storage.move(source, dest)
        self.assertTrue(result)
        self.assertFalse(source.exists())
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "content")

    def test_zip_creation(self):
        (self.temp_dir / "file1.txt").write_text("content1")
        (self.temp_dir / "file2.txt").write_text("content2")
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        storage = self.make_storage()
        zip_content = storage.create_zip([self.temp_dir])
        self.assertIsNotNone(zip_content)
        self.assertGreater(len(zip_content), 0)

    def test_text_detection(self):
        storage = self.make_storage()
        text_file = self.temp_dir / "test.txt"
        text_file.write_text("Hello")
        self.assertTrue(storage.is_text_file(text_file))

        bin_file = self.temp_dir / "test.bin"
        bin_file.write_bytes(b"\x00\x01\x02")
        self.assertFalse(storage.is_text_file(bin_file))

    def test_hidden_files(self):
        (self.temp_dir / ".hidden").write_text("hidden content")
        (self.temp_dir / "visible.txt").write_text("visible content")

        storage_no_hidden = self.make_storage(show_hidden=False)
        files = storage_no_hidden.list_directory(self.temp_dir)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "visible.txt")

        storage_with_hidden = self.make_storage(show_hidden=True)
        files = storage_with_hidden.list_directory(self.temp_dir)
        self.assertEqual(len(files), 2)


class TestRootDeletionGuard(BaseServerTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.temp_dir / "test.txt").write_text("content")

    def test_cannot_delete_root(self):
        body, status = self._post('/delete', {'p': ''})
        self.assertEqual(status, 400)
        self.assertTrue(self.temp_dir.exists())

    def test_cannot_move_root(self):
        body, status = self._post('/move', {'source': '', 'destination': 'moved'})
        self.assertEqual(status, 400)
        self.assertTrue(self.temp_dir.exists())

    def test_cannot_copy_root(self):
        body, status = self._post('/copy', {'source': '', 'destination': 'copy'})
        self.assertEqual(status, 400)


class TestMultipartParser(unittest.TestCase):
    def test_extract_csrf_from_multipart(self):
        body = (
            b'--boundary\r\n'
            b'Content-Disposition: form-data; name="_csrf"\r\n'
            b'\r\n'
            b'test-token-value\r\n'
            b'--boundary--\r\n'
        )
        result = FileServerHandler._extract_csrf_from_multipart(None, body)
        self.assertEqual(result, 'test-token-value')

    def test_extract_csrf_from_multipart_no_token(self):
        body = (
            b'--boundary\r\n'
            b'Content-Disposition: form-data; name="other"\r\n'
            b'\r\n'
            b'value\r\n'
            b'--boundary--\r\n'
        )
        result = FileServerHandler._extract_csrf_from_multipart(None, body)
        self.assertEqual(result, '')

    def test_extract_csrf_from_multipart_empty_body(self):
        result = FileServerHandler._extract_csrf_from_multipart(None, b'')
        self.assertEqual(result, '')


class TestGetMultipartData(unittest.TestCase):
    def test_no_multipart_content_type(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        handler._buffered_body = b'foo=bar'
        handler.config.server.max_upload_size = 104857600
        fields, files = FileServerHandler._get_multipart_data(handler)
        self.assertEqual(fields, {})
        self.assertEqual(files, {})

    def test_no_boundary(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = {'Content-Type': 'multipart/form-data'}
        handler._buffered_body = b'--boundary\r\n'
        handler.config.server.max_upload_size = 104857600
        fields, files = FileServerHandler._get_multipart_data(handler)
        self.assertEqual(fields, {})
        self.assertEqual(files, {})

    def test_no_buffered_body(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = {'Content-Type': 'multipart/form-data; boundary=abc'}
        handler._buffered_body = None
        handler.config.server.max_upload_size = 104857600
        fields, files = FileServerHandler._get_multipart_data(handler)
        self.assertEqual(fields, {})
        self.assertEqual(files, {})

    def test_upload_too_large(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = {'Content-Type': 'multipart/form-data; boundary=abc'}
        handler._buffered_body = b'x' * 100
        handler.config.server.max_upload_size = 50
        with self.assertRaises(ValueError):
            FileServerHandler._get_multipart_data(handler)

    def test_parse_simple_multipart(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = {'Content-Type': 'multipart/form-data; boundary=BOUNDARY'}
        body = (
            b'--BOUNDARY\r\n'
            b'Content-Disposition: form-data; name="field1"\r\n'
            b'\r\n'
            b'value1\r\n'
            b'--BOUNDARY\r\n'
            b'Content-Disposition: form-data; name="file1"; filename="test.txt"\r\n'
            b'Content-Type: text/plain\r\n'
            b'\r\n'
            b'file content\r\n'
            b'--BOUNDARY--\r\n'
        )
        handler._buffered_body = body
        handler.config.server.max_upload_size = 104857600
        fields, files = FileServerHandler._get_multipart_data(handler)
        self.assertIn('field1', fields)
        self.assertEqual(fields['field1'], 'value1')
        self.assertIn('file1', files)
        self.assertEqual(files['file1'][0], 'test.txt')
        self.assertEqual(files['file1'][1], b'file content')

    def test_parse_multipart_with_newline_boundaries(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = {'Content-Type': 'multipart/form-data; boundary=B'}
        body = (
            b'--B\n'
            b'Content-Disposition: form-data; name="f"\n'
            b'\n'
            b'v\n'
            b'--B--\n'
        )
        handler._buffered_body = body
        handler.config.server.max_upload_size = 104857600
        fields, files = FileServerHandler._get_multipart_data(handler)
        self.assertIn('f', fields)
        self.assertEqual(fields['f'], 'v')


class TestCheckFeature(unittest.TestCase):
    def test_feature_enabled(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.config.features.edit = True
        result = FileServerHandler._check_feature(handler, 'edit', 'Editing')
        self.assertTrue(result)

    def test_feature_disabled(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.config.features.edit = False
        result = FileServerHandler._check_feature(handler, 'edit', 'Editing')
        self.assertFalse(result)


class TestResolvePath(BaseTest):
    def test_resolve_valid(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.config.get_root_path.return_value = self.temp_dir
        (self.temp_dir / 'test.txt').write_text('content')
        result = FileServerHandler._resolve_path(handler, 'test.txt')
        self.assertEqual(result, self.temp_dir / 'test.txt')

    def test_resolve_traversal(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.config.get_root_path.return_value = self.temp_dir
        result = FileServerHandler._resolve_path(handler, '../etc/passwd')
        self.assertIsNone(result)


class TestGetFormData(unittest.TestCase):
    def test_urlencoded_form(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        handler._buffered_body = b'key1=value1&key2=value2'
        result = FileServerHandler._get_form_data(handler)
        self.assertEqual(result['key1'], 'value1')
        self.assertEqual(result['key2'], 'value2')

    def test_no_body(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        handler._buffered_body = None
        result = FileServerHandler._get_form_data(handler)
        self.assertEqual(result, {})

    def test_wrong_content_type(self):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = {'Content-Type': 'multipart/form-data'}
        handler._buffered_body = b'foo=bar'
        result = FileServerHandler._get_form_data(handler)
        self.assertEqual(result, {})
if __name__ == "__main__":
    unittest.main()
