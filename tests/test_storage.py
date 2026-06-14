"""
Tests for storage module.
"""

import unittest
import tempfile
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.storage import Storage, FileInfo, format_size, format_time


class TestStorage(unittest.TestCase):
    """Test storage operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = Path(tempfile.mkdtemp())
        self.storage = Storage(self.root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.root, ignore_errors=True)

    def test_list_empty_directory(self):
        """Test listing empty directory."""
        files = self.storage.list_directory(self.root)
        self.assertEqual(len(files), 0)

    def test_list_directory_with_files(self):
        """Test listing directory with files."""
        # Create test files
        (self.root / "test1.txt").touch()
        (self.root / "test2.txt").touch()
        (self.root / "subdir").mkdir()

        files = self.storage.list_directory(self.root)
        self.assertEqual(len(files), 3)

        # Check sorting (directories first)
        self.assertTrue(files[0].is_dir)
        self.assertEqual(files[0].name, "subdir")

    def test_create_directory(self):
        """Test directory creation."""
        target = self.root / "newdir"
        result = self.storage.create_directory(target)
        self.assertTrue(result)
        self.assertTrue(target.exists())
        self.assertTrue(target.is_dir())

    def test_write_and_read_file(self):
        """Test file write and read."""
        target = self.root / "test.txt"
        content = b"Hello, World!"

        result = self.storage.write_file(target, content)
        self.assertTrue(result)
        self.assertTrue(target.exists())

        read_content = self.storage.read_file(target)
        self.assertEqual(read_content, content)

    def test_write_and_read_text_file(self):
        """Test text file write and read."""
        target = self.root / "test.txt"
        content = "Hello, World!"

        result = self.storage.write_text_file(target, content)
        self.assertTrue(result)

        read_content = self.storage.read_text_file(target)
        self.assertEqual(read_content, content)

    def test_delete_file(self):
        """Test file deletion."""
        target = self.root / "test.txt"
        target.touch()

        result = self.storage.delete_file(target)
        self.assertTrue(result)
        self.assertFalse(target.exists())

    def test_delete_directory(self):
        """Test directory deletion."""
        target = self.root / "testdir"
        target.mkdir()
        (target / "file.txt").touch()

        result = self.storage.delete_file(target)
        self.assertTrue(result)
        self.assertFalse(target.exists())

    def test_move_file(self):
        """Test file move."""
        source = self.root / "source.txt"
        source.write_text("content")
        dest = self.root / "dest.txt"

        result = self.storage.move(source, dest)
        self.assertTrue(result)
        self.assertFalse(source.exists())
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "content")

    def test_copy_file(self):
        """Test file copy."""
        source = self.root / "source.txt"
        source.write_text("content")
        dest = self.root / "dest.txt"

        result = self.storage.copy(source, dest)
        self.assertTrue(result)
        self.assertTrue(source.exists())
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "content")

    def test_search(self):
        """Test file search."""
        (self.root / "test1.txt").touch()
        (self.root / "test2.txt").touch()
        (self.root / "other.txt").touch()

        results = self.storage.search("test")
        self.assertEqual(len(results), 2)

    def test_get_file_info(self):
        """Test getting file info."""
        target = self.root / "test.txt"
        target.write_text("Hello")

        info = self.storage.get_file_info(target)
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "test.txt")
        self.assertFalse(info.is_dir)
        self.assertEqual(info.size, 5)

    def test_is_text_file(self):
        """Test text file detection."""
        # Text file
        text_file = self.root / "test.txt"
        text_file.write_text("Hello")
        self.assertTrue(self.storage.is_text_file(text_file))

        # Binary file
        bin_file = self.root / "test.bin"
        bin_file.write_bytes(b"\x00\x01\x02")
        self.assertFalse(self.storage.is_text_file(bin_file))

    def test_create_zip(self):
        """Test ZIP creation."""
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


class TestFormatSize(unittest.TestCase):
    """Test size formatting."""

    def test_bytes(self):
        """Test byte formatting."""
        self.assertEqual(format_size(0), "0B")
        self.assertEqual(format_size(100), "100B")

    def test_kilobytes(self):
        """Test kilobyte formatting."""
        self.assertEqual(format_size(1024), "1.0KB")
        self.assertEqual(format_size(1536), "1.5KB")

    def test_megabytes(self):
        """Test megabyte formatting."""
        self.assertEqual(format_size(1048576), "1.0MB")

    def test_gigabytes(self):
        """Test gigabyte formatting."""
        self.assertEqual(format_size(1073741824), "1.0GB")


class TestFormatTime(unittest.TestCase):
    """Test time formatting."""

    def test_format_time(self):
        """Test time formatting."""
        import time
        timestamp = time.time()
        result = format_time(timestamp)
        self.assertIsNotNone(result)
        self.assertIn("-", result)
        self.assertIn(":", result)


if __name__ == "__main__":
    unittest.main()
