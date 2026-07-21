"""
Tests for utility modules.
"""

import unittest
import os

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.utils.mime import guess_mime_type, is_text_mime_type, get_extension, is_image_mime_type, get_content_disposition
from server.utils.format import format_size, format_time, escape_html, format_permissions
from server.utils.path import normalize_path, join_paths, get_parent_path

class TestMimeUtils(unittest.TestCase):
    """Test MIME type utilities."""

    def test_guess_mime_type_text(self):
        """Test MIME type for text files."""
        self.assertEqual(guess_mime_type("test.txt"), "text/plain")
        self.assertEqual(guess_mime_type("test.py"), "text/x-python")
        self.assertEqual(guess_mime_type("test.js"), "application/javascript")

    def test_guess_mime_type_image(self):
        """Test MIME type for image files."""
        self.assertEqual(guess_mime_type("test.png"), "image/png")
        self.assertEqual(guess_mime_type("test.jpg"), "image/jpeg")
        self.assertEqual(guess_mime_type("test.gif"), "image/gif")

    def test_guess_mime_type_unknown(self):
        """Test MIME type for unknown files."""
        result = guess_mime_type("test.xyz123")
        # Should return None or a default
        self.assertTrue(result is None or isinstance(result, str))

    def test_is_text_mime_type(self):
        """Test text MIME type detection."""
        self.assertTrue(is_text_mime_type("text/plain"))
        self.assertTrue(is_text_mime_type("text/html"))
        self.assertTrue(is_text_mime_type("application/json"))
        self.assertFalse(is_text_mime_type("image/png"))
        self.assertFalse(is_text_mime_type("video/mp4"))

    def test_get_extension(self):
        """Test extension extraction."""
        self.assertEqual(get_extension("test.txt"), ".txt")
        self.assertEqual(get_extension("test.PY"), ".py")
        self.assertEqual(get_extension("test"), "")

    def test_is_image_mime_type(self):
        """Test image MIME type detection."""
        self.assertTrue(is_image_mime_type('image/png'))
        self.assertTrue(is_image_mime_type('image/jpeg'))
        self.assertFalse(is_image_mime_type('text/plain'))
        self.assertFalse(is_image_mime_type('video/mp4'))

    def test_get_content_disposition_inline(self):
        """Test inline disposition for text/images."""
        disp = get_content_disposition('test.txt', 'text/plain')
        self.assertIn('inline', disp)
        self.assertIn('test.txt', disp)

    def test_get_content_disposition_attachment(self):
        """Test attachment disposition for binary files."""
        disp = get_content_disposition('file.zip', 'application/zip')
        self.assertIn('attachment', disp)
        self.assertIn('file.zip', disp)

class TestFormatUtils(unittest.TestCase):
    """Test formatting utilities."""

    def test_format_size_bytes(self):
        """Test byte formatting."""
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(100), "100 B")

    def test_format_size_kilobytes(self):
        """Test kilobyte formatting."""
        result = format_size(1024)
        self.assertIn("KB", result)

    def test_format_size_megabytes(self):
        """Test megabyte formatting."""
        result = format_size(1024 * 1024)
        self.assertIn("MB", result)

    def test_format_time(self):
        """Test time formatting."""
        import time
        timestamp = time.time()
        result = format_time(timestamp)
        self.assertIsNotNone(result)
        self.assertIn("-", result)

    def test_escape_html_all_chars(self):
        self.assertEqual(escape_html("<>&\"'"), "&lt;&gt;&amp;&quot;&#39;")
        self.assertEqual(escape_html("hello"), "hello")
        self.assertEqual(escape_html(""), "")

    def test_format_permissions(self):
        # Regular file: -rw-r--r--
        self.assertEqual(format_permissions(0o644), '-rw-r--r--')
        # Directory: drwxr-xr-x
        self.assertEqual(format_permissions(0o755 | 0o040000), 'drwxr-xr-x')
        # Executable: -rwxr-xr-x
        self.assertEqual(format_permissions(0o755), '-rwxr-xr-x')
        # Symlink
        self.assertEqual(format_permissions(0o777 | 0o120000), 'lrwxrwxrwx')

class TestPathUtils(unittest.TestCase):
    def test_normalize_path(self):
        self.assertEqual(normalize_path("/foo/bar"), "foo/bar")
        self.assertEqual(normalize_path("foo//bar"), "foo/bar")
        self.assertEqual(normalize_path("foo/./bar"), "foo/bar")
        self.assertEqual(normalize_path(""), "")
        self.assertEqual(normalize_path("/"), "")
        self.assertEqual(normalize_path("foo"), "foo")

    def test_normalize_path_traversal(self):
        result = normalize_path("foo/../bar")
        self.assertEqual(result, "bar")
        result = normalize_path("foo/../../bar")
        self.assertEqual(result, "bar")

    def test_join_paths(self):
        self.assertEqual(join_paths("foo", "bar"), "foo/bar")
        self.assertEqual(join_paths("/foo", "bar"), "foo/bar")
        self.assertEqual(join_paths("foo/", "/bar"), "foo/bar")
        self.assertEqual(join_paths(), "")
        self.assertEqual(join_paths("foo"), "foo")
        self.assertEqual(join_paths("", "foo"), "foo")

    def test_get_parent_path(self):
        self.assertEqual(get_parent_path("foo/bar"), "foo")
        self.assertEqual(get_parent_path("foo"), "")
        self.assertEqual(get_parent_path(""), "")
        self.assertEqual(get_parent_path("/"), "")
        self.assertEqual(get_parent_path("a/b/c"), "a/b")


class TestMimeUtilsExtended(unittest.TestCase):
    def test_get_extension_special(self):
        self.assertEqual(get_extension("Makefile"), ".makefile")
        self.assertEqual(get_extension("Dockerfile"), ".dockerfile")
        self.assertEqual(get_extension(".gitignore"), ".gitignore")
        self.assertEqual(get_extension("CMakeLists.txt"), ".cmakelists.txt")

    def test_guess_mime_type_more(self):
        self.assertEqual(guess_mime_type("test.md"), "text/markdown")
        self.assertEqual(guess_mime_type("test.yaml"), "text/yaml")
        self.assertEqual(guess_mime_type("test.yml"), "text/yaml")
        self.assertEqual(guess_mime_type("test.json"), "application/json")
        self.assertEqual(guess_mime_type("test.xml"), "application/xml")
        self.assertEqual(guess_mime_type("test.csv"), "text/csv")
        self.assertEqual(guess_mime_type("test.sh"), "text/x-shellscript")
        self.assertEqual(guess_mime_type("test.go"), "text/x-go")
        self.assertEqual(guess_mime_type("test.rs"), "text/x-rust")
        self.assertEqual(guess_mime_type("test.mp4"), "video/mp4")
        self.assertEqual(guess_mime_type("test.mp3"), "audio/mpeg")
        self.assertEqual(guess_mime_type("test.pdf"), "application/pdf")

    def test_is_text_mime_type_more(self):
        self.assertTrue(is_text_mime_type("text/css"))
        self.assertTrue(is_text_mime_type("text/javascript"))
        self.assertTrue(is_text_mime_type("application/xml"))
        self.assertTrue(is_text_mime_type("application/yaml"))
        self.assertFalse(is_text_mime_type(""))
        self.assertFalse(is_text_mime_type(None))
        self.assertFalse(is_text_mime_type("application/zip"))

    def test_is_image_mime_type_more(self):
        self.assertTrue(is_image_mime_type('image/webp'))
        self.assertTrue(is_image_mime_type('image/svg+xml'))
        self.assertTrue(is_image_mime_type('image/gif'))
        self.assertFalse(is_image_mime_type(''))
        self.assertFalse(is_image_mime_type(None))
        self.assertFalse(is_image_mime_type('application/pdf'))

    def test_get_content_disposition_special_chars(self):
        disp = get_content_disposition('file name.txt', 'text/plain')
        self.assertIn('inline', disp)
        self.assertIn('file%20name.txt', disp)

    def test_get_content_disposition_no_mime(self):
        disp = get_content_disposition('file.bin', None)
        self.assertIn('attachment', disp)

if __name__ == "__main__":
    unittest.main()
