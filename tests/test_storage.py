import unittest
import os
from pathlib import Path

from tests.base import BaseTest
from server.storage import Storage, FileInfo, format_size, format_time, get_icon_for_file


class TestStorage(BaseTest):
    def setUp(self):
        super().setUp()
        self.storage = Storage(self.temp_dir)

    def test_list_empty_directory(self):
        files = self.storage.list_directory(self.temp_dir)
        self.assertEqual(len(files), 0)

    def test_list_directory_with_files(self):
        (self.temp_dir / "test1.txt").touch()
        (self.temp_dir / "test2.txt").touch()
        (self.temp_dir / "subdir").mkdir()

        files = self.storage.list_directory(self.temp_dir)
        self.assertEqual(len(files), 3)
        self.assertTrue(files[0].is_dir)
        self.assertEqual(files[0].name, "subdir")

    def test_create_directory(self):
        target = self.temp_dir / "newdir"
        result = self.storage.create_directory(target)
        self.assertTrue(result)
        self.assertTrue(target.exists())
        self.assertTrue(target.is_dir())

    def test_write_and_read_file(self):
        target = self.temp_dir / "test.txt"
        content = b"Hello, World!"

        result = self.storage.write_file(target, content)
        self.assertTrue(result)
        self.assertTrue(target.exists())

        read_content = self.storage.read_file(target)
        self.assertEqual(read_content, content)

    def test_write_and_read_text_file(self):
        target = self.temp_dir / "test.txt"
        content = "Hello, World!"

        result = self.storage.write_text_file(target, content)
        self.assertTrue(result)

        read_content = self.storage.read_text_file(target)
        self.assertEqual(read_content, content)

    def test_delete_file(self):
        target = self.temp_dir / "test.txt"
        target.touch()

        result = self.storage.delete_file(target)
        self.assertTrue(result)
        self.assertFalse(target.exists())

    def test_delete_directory(self):
        target = self.temp_dir / "testdir"
        target.mkdir()
        (target / "file.txt").touch()

        result = self.storage.delete_file(target)
        self.assertTrue(result)
        self.assertFalse(target.exists())

    def test_move_file(self):
        source = self.temp_dir / "source.txt"
        source.write_text("content")
        dest = self.temp_dir / "dest.txt"

        result = self.storage.move(source, dest)
        self.assertTrue(result)
        self.assertFalse(source.exists())
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "content")

    def test_copy_file(self):
        source = self.temp_dir / "source.txt"
        source.write_text("content")
        dest = self.temp_dir / "dest.txt"

        result = self.storage.copy(source, dest)
        self.assertTrue(result)
        self.assertTrue(source.exists())
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "content")

    def test_search(self):
        (self.temp_dir / "test1.txt").touch()
        (self.temp_dir / "test2.txt").touch()
        (self.temp_dir / "other.txt").touch()

        results = self.storage.search("test")
        self.assertEqual(len(results), 2)

    def test_get_file_info(self):
        target = self.temp_dir / "test.txt"
        target.write_text("Hello")

        info = self.storage.get_file_info(target)
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "test.txt")
        self.assertFalse(info.is_dir)
        self.assertEqual(info.size, 5)

    def test_is_text_file(self):
        text_file = self.temp_dir / "test.txt"
        text_file.write_text("Hello")
        self.assertTrue(self.storage.is_text_file(text_file))

        bin_file = self.temp_dir / "test.bin"
        bin_file.write_bytes(b"\x00\x01\x02")
        self.assertFalse(self.storage.is_text_file(bin_file))

    def test_create_zip(self):
        (self.temp_dir / "file1.txt").write_text("content1")
        (self.temp_dir / "file2.txt").write_text("content2")
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        zip_content = self.storage.create_zip([self.temp_dir])
        self.assertIsNotNone(zip_content)
        self.assertGreater(len(zip_content), 0)


class TestFormatSize(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(100), "100 B")

    def test_kilobytes(self):
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1536), "1.5 KB")

    def test_megabytes(self):
        self.assertEqual(format_size(1048576), "1.0 MB")

    def test_gigabytes(self):
        self.assertEqual(format_size(1073741824), "1.0 GB")


class TestFormatTime(unittest.TestCase):
    def test_format_time(self):
        import time
        timestamp = time.time()
        result = format_time(timestamp)
        self.assertIsNotNone(result)
        self.assertIn("-", result)
        self.assertIn(":", result)


class TestGetIconForFile(unittest.TestCase):
    def test_folder_icon(self):
        self.assertEqual(get_icon_for_file('mydir', True), '📁')

    def test_python_file(self):
        self.assertEqual(get_icon_for_file('test.py', False), '🐍')

    def test_javascript_file(self):
        self.assertEqual(get_icon_for_file('app.js', False), '📜')

    def test_image_file(self):
        self.assertEqual(get_icon_for_file('photo.jpg', False), '🖼️')

    def test_unknown_file(self):
        self.assertEqual(get_icon_for_file('file.xyz', False), '📄')


class TestFileInfo(unittest.TestCase):
    def test_to_dict(self):
        info = FileInfo(
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
        d = info.to_dict()
        self.assertEqual(d['name'], 'test.txt')
        self.assertEqual(d['path'], 'test.txt')
        self.assertFalse(d['is_dir'])
        self.assertEqual(d['size'], 1024)
        self.assertIn('size_formatted', d)
        self.assertEqual(d['mime_type'], 'text/plain')
        self.assertTrue(d['is_text'])


if __name__ == "__main__":
    unittest.main()
