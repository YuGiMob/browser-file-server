import unittest
import os
import json
from pathlib import Path

from tests.base import BaseTest
from server.storage import Storage


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


if __name__ == "__main__":
    unittest.main()
