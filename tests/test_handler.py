"""
Tests for HTTP handler.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.config import Config, ServerConfig, SecurityConfig, FeaturesConfig, UIConfig, LoggingConfig, RateLimitConfig
from server.storage import Storage


class TestHandlerIntegration(unittest.TestCase):
    """Integration tests for handler."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = Path(tempfile.mkdtemp())
        self.config = Config(
            server=ServerConfig(root=str(self.root)),
            security=SecurityConfig(rate_limit=RateLimitConfig(enabled=False)),
            features=FeaturesConfig(),
            ui=UIConfig(),
            logging=LoggingConfig(),
        )
        self.storage = Storage(self.root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.root, ignore_errors=True)

    def test_directory_listing(self):
        """Test directory listing with multiple files."""
        # Create test files
        (self.root / "file1.txt").write_text("content1")
        (self.root / "file2.txt").write_text("content2")
        (self.root / "subdir").mkdir()

        # List directory
        files = self.storage.list_directory(self.root)
        self.assertEqual(len(files), 3)

        # Check sorting (directories first)
        self.assertTrue(files[0].is_dir)
        self.assertEqual(files[0].name, "subdir")

    def test_file_operations(self):
        """Test file operations."""
        # Test write
        (self.root / "test.txt").write_text("Hello")
        self.assertEqual((self.root / "test.txt").read_text(), "Hello")

        # Test rename
        (self.root / "test.txt").rename(self.root / "renamed.txt")
        self.assertFalse((self.root / "test.txt").exists())
        self.assertTrue((self.root / "renamed.txt").exists())

        # Test delete
        (self.root / "renamed.txt").unlink()
        self.assertFalse((self.root / "renamed.txt").exists())

    def test_file_search(self):
        """Test file search functionality."""
        # Create test files
        (self.root / "test1.txt").write_text("content1")
        (self.root / "test2.txt").write_text("content2")
        (self.root / "other.txt").write_text("content3")

        # Search
        results = self.storage.search("test")
        self.assertEqual(len(results), 2)

    def test_file_info(self):
        """Test file info retrieval."""
        # Create test file
        (self.root / "test.txt").write_text("Hello, World!")

        # Get file info
        info = self.storage.get_file_info(self.root / "test.txt")
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "test.txt")
        self.assertFalse(info.is_dir)
        self.assertEqual(info.size, 13)
        self.assertTrue(info.is_text)

    def test_directory_creation(self):
        """Test directory creation."""
        target = self.root / "newdir"
        result = self.storage.create_directory(target)
        self.assertTrue(result)
        self.assertTrue(target.exists())
        self.assertTrue(target.is_dir())

    def test_file_copy(self):
        """Test file copy."""
        source = self.root / "source.txt"
        source.write_text("content")
        dest = self.root / "dest.txt"

        result = self.storage.copy(source, dest)
        self.assertTrue(result)
        self.assertTrue(source.exists())
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "content")

    def test_file_move(self):
        """Test file move."""
        source = self.root / "source.txt"
        source.write_text("content")
        dest = self.root / "dest.txt"

        result = self.storage.move(source, dest)
        self.assertTrue(result)
        self.assertFalse(source.exists())
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "content")

    def test_zip_creation(self):
        """Test ZIP file creation."""
        # Create test files
        (self.root / "file1.txt").write_text("content1")
        (self.root / "file2.txt").write_text("content2")
        subdir = self.root / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        # Create ZIP
        zip_content = self.storage.create_zip([self.root])
        self.assertIsNotNone(zip_content)
        self.assertGreater(len(zip_content), 0)

    def test_text_detection(self):
        """Test text file detection."""
        # Text file
        text_file = self.root / "test.txt"
        text_file.write_text("Hello")
        self.assertTrue(self.storage.is_text_file(text_file))

        # Binary file
        bin_file = self.root / "test.bin"
        bin_file.write_bytes(b"\x00\x01\x02")
        self.assertFalse(self.storage.is_text_file(bin_file))

    def test_hidden_files(self):
        """Test hidden file handling."""
        # Create hidden file
        (self.root / ".hidden").write_text("hidden content")
        (self.root / "visible.txt").write_text("visible content")

        # List without hidden files
        storage_no_hidden = Storage(self.root, show_hidden=False)
        files = storage_no_hidden.list_directory(self.root)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "visible.txt")

        # List with hidden files
        storage_with_hidden = Storage(self.root, show_hidden=True)
        files = storage_with_hidden.list_directory(self.root)
        self.assertEqual(len(files), 2)


if __name__ == "__main__":
    unittest.main()
