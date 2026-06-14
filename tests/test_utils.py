"""
Tests for utility modules.
"""

import unittest
import os

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.utils.mime import guess_mime_type, is_text_mime_type, get_extension
from server.utils.format import format_size, format_time, escape_html, unescape_html
from server.utils.path import normalize_path, join_paths, get_parent_path, get_filename


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

    def test_escape_html(self):
        """Test HTML escaping."""
        self.assertEqual(escape_html("<b>bold</b>"), "&lt;b&gt;bold&lt;/b&gt;")
        self.assertEqual(escape_html("a & b"), "a &amp; b")
        self.assertEqual(escape_html('"quotes"'), "&quot;quotes&quot;")

    def test_unescape_html(self):
        """Test HTML unescaping."""
        self.assertEqual(unescape_html("&lt;b&gt;bold&lt;/b&gt;"), "<b>bold</b>")
        self.assertEqual(unescape_html("a &amp; b"), "a & b")


class TestPathUtils(unittest.TestCase):
    """Test path utilities."""

    def test_normalize_path(self):
        """Test path normalization."""
        self.assertEqual(normalize_path("/foo/bar"), "foo/bar")
        self.assertEqual(normalize_path("foo//bar"), "foo/bar")
        self.assertEqual(normalize_path("foo/./bar"), "foo/bar")

    def test_normalize_path_traversal(self):
        """Test path normalization with traversal."""
        result = normalize_path("foo/../bar")
        self.assertEqual(result, "bar")

    def test_join_paths(self):
        """Test path joining."""
        self.assertEqual(join_paths("foo", "bar"), "foo/bar")
        self.assertEqual(join_paths("/foo", "bar"), "foo/bar")
        self.assertEqual(join_paths("foo/", "/bar"), "foo/bar")

    def test_get_parent_path(self):
        """Test getting parent path."""
        self.assertEqual(get_parent_path("foo/bar"), "foo")
        self.assertEqual(get_parent_path("foo"), "")
        self.assertEqual(get_parent_path(""), "")

    def test_get_filename(self):
        """Test getting filename."""
        self.assertEqual(get_filename("foo/bar.txt"), "bar.txt")
        self.assertEqual(get_filename("foo"), "foo")
        self.assertEqual(get_filename(""), "")


if __name__ == "__main__":
    unittest.main()
