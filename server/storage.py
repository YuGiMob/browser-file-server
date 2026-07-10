"""
File storage operations.

Provides:
- File/directory CRUD operations
- Search functionality
- File metadata
- Archive creation
"""

import os
import shutil
import zipfile
import io
import time
from pathlib import Path
from typing import List, Dict, Optional, Generator, Any
from dataclasses import dataclass
import mimetypes

from .utils.format import format_size, format_time


@dataclass
class FileInfo:
    """File/directory information."""
    name: str
    path: str  # Relative path from root
    is_dir: bool
    size: int
    modified: float
    modified_str: str
    mime_type: Optional[str]
    is_text: bool
    is_hidden: bool
    permissions: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "is_dir": self.is_dir,
            "size": self.size,
            "size_formatted": format_size(self.size),
            "modified": self.modified,
            "modified_str": self.modified_str,
            "mime_type": self.mime_type,
            "is_text": self.is_text,
            "is_hidden": self.is_hidden,
            "permissions": self.permissions,
        }


# Text file extensions
TEXT_EXTENSIONS = {
    ".sh", ".bash", ".zsh", ".fish", ".py", ".pyw", ".js", ".ts", ".mjs", ".cjs",
    ".jsx", ".tsx", ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".conf", ".cfg",
    ".md", ".markdown", ".txt", ".log", ".csv", ".tsv", ".rtf",
    ".go", ".rs", ".java", ".kt", ".scala", ".c", ".h", ".cpp", ".hpp", ".cc",
    ".cs", ".vb", ".rb", ".php", ".pl", ".pm", ".lua", ".r", ".R", ".sql",
    ".diff", ".patch", ".gitignore", ".gitattributes", ".editorconfig",
    ".dockerfile", ".env", ".env.example", ".env.local",
    ".vim", ".el", ".clj", ".ex", ".exs", ".erl", ".hs",
    ".swift", ".dart", ".vue", ".svelte", ".astro",
    ".makefile", ".cmake", ".gradle",
    ".properties", ".toml", ".cfg", ".ini",
    ".rst", ".asciidoc", ".textile",
    ".org", ".tex", ".latex",
}

# Binary file extensions that should be previewed
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv", ".flv", ".wmv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".wma", ".m4a"}
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"}


class Storage:
    """File storage operations."""

    def __init__(self, root: Path, show_hidden: bool = False):
        """
        Initialize storage.

        Args:
            root: Root directory path
            show_hidden: Whether to show hidden files
        """
        self.root = root.resolve()
        self.show_hidden = show_hidden

    def get_file_info(self, path: Path, relative_to: Optional[Path] = None) -> Optional[FileInfo]:
        """
        Get file information.

        Args:
            path: Absolute path to file
            relative_to: Base path for relative path calculation

        Returns:
            FileInfo object or None if file doesn't exist
        """
        try:
            stat = path.stat()
        except (OSError, PermissionError):
            return None

        relative_base = relative_to or self.root
        try:
            rel_path = str(path.relative_to(relative_base))
        except ValueError:
            rel_path = path.name

        name = path.name
        is_dir = path.is_dir()
        mime_type = None
        is_text = False

        if not is_dir:
            mime_type, _ = mimetypes.guess_type(str(path))
            is_text = self.is_text_file(path)

        # Get permissions string
        permissions = self._format_permissions(stat.st_mode)

        return FileInfo(
            name=name,
            path=rel_path,
            is_dir=is_dir,
            size=stat.st_size if not is_dir else 0,
            modified=stat.st_mtime,
            modified_str=format_time(stat.st_mtime),
            mime_type=mime_type,
            is_text=is_text,
            is_hidden=name.startswith('.'),
            permissions=permissions,
        )

    def list_directory(
        self,
        path: Path,
        sort_by: str = "name",
        show_hidden: Optional[bool] = None,
    ) -> List[FileInfo]:
        """
        List directory contents.

        Args:
            path: Directory path
            sort_by: Sort field (name, size, modified)
            show_hidden: Override show_hidden setting

        Returns:
            List of FileInfo objects
        """
        if not path.is_dir():
            return []

        show = show_hidden if show_hidden is not None else self.show_hidden
        entries = []

        try:
            for item in path.iterdir():
                # Skip hidden files if not showing them
                if not show and item.name.startswith('.'):
                    continue

                info = self.get_file_info(item)
                if info:
                    entries.append(info)
        except PermissionError:
            pass

        # Sort entries
        reverse = False
        if sort_by == "size":
            key = lambda x: (not x.is_dir, x.size)
        elif sort_by == "modified":
            key = lambda x: (not x.is_dir, -x.modified)
            reverse = True
        else:  # name
            key = lambda x: (not x.is_dir, x.name.lower())

        entries.sort(key=key, reverse=reverse)

        return entries

    def read_file(self, path: Path) -> Optional[bytes]:
        """
        Read file contents.

        Args:
            path: File path

        Returns:
            File contents or None
        """
        try:
            return path.read_bytes()
        except (OSError, PermissionError):
            return None

    def read_text_file(self, path: Path, encoding: str = "utf-8") -> Optional[str]:
        """
        Read text file contents.

        Args:
            path: File path
            encoding: File encoding

        Returns:
            File contents as string or None
        """
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except (OSError, PermissionError):
            return None

    def write_file(self, path: Path, content: bytes) -> bool:
        """
        Write content to file.

        Args:
            path: File path
            content: File content

        Returns:
            True if successful
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            return True
        except (OSError, PermissionError):
            return False

    def write_text_file(self, path: Path, content: str, encoding: str = "utf-8") -> bool:
        """
        Write text content to file.

        Args:
            path: File path
            content: File content
            encoding: File encoding

        Returns:
            True if successful
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)
            return True
        except (OSError, PermissionError):
            return False

    def delete_file(self, path: Path) -> bool:
        """
        Delete a file.

        Args:
            path: File path

        Returns:
            True if successful
        """
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return True
        except (OSError, PermissionError):
            return False

    def create_directory(self, path: Path) -> bool:
        """
        Create a directory.

        Args:
            path: Directory path

        Returns:
            True if successful
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False

    def move(self, source: Path, destination: Path) -> bool:
        """
        Move/rename a file or directory.

        Args:
            source: Source path
            destination: Destination path

        Returns:
            True if successful
        """
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            return True
        except (OSError, PermissionError):
            return False

    def copy(self, source: Path, destination: Path) -> bool:
        """
        Copy a file or directory.

        Args:
            source: Source path
            destination: Destination path

        Returns:
            True if successful
        """
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(str(source), str(destination))
            else:
                # Try shutil.copy2 first, fall back to manual copy
                try:
                    shutil.copy2(str(source), str(destination))
                except PermissionError:
                    # Fallback: read and write manually
                    content = source.read_bytes()
                    destination.write_bytes(content)
            return True
        except (OSError, PermissionError):
            return False

    def search(
        self,
        query: str,
        path: Optional[Path] = None,
        max_results: int = 100,
        show_hidden: Optional[bool] = None,
    ) -> List[FileInfo]:
        """
        Search for files by name.

        Args:
            query: Search query
            path: Directory to search in (default: root)
            max_results: Maximum number of results
            show_hidden: Override show_hidden setting (default: use instance setting)

        Returns:
            List of matching FileInfo objects
        """
        search_path = path or self.root
        query_lower = query.lower()
        results = []
        show = show_hidden if show_hidden is not None else self.show_hidden

        for item in self._walk_directory(search_path, show_hidden=show):
            if query_lower in item.name.lower():
                results.append(item)
                if len(results) >= max_results:
                    break

        return results

    def _walk_directory(self, path: Path, show_hidden: Optional[bool] = None) -> Generator[FileInfo, None, None]:
        """Walk directory recursively."""
        show = show_hidden if show_hidden is not None else self.show_hidden
        try:
            for item in path.iterdir():
                # Skip hidden files if not showing them
                if not show and item.name.startswith('.'):
                    continue

                info = self.get_file_info(item)
                if info:
                    yield info

                    if item.is_dir():
                        yield from self._walk_directory(item, show_hidden=show)
        except (PermissionError, OSError):
            pass

    def create_zip(self, paths: List[Path]) -> Optional[bytes]:
        """
        Create a ZIP archive from multiple files/directories.

        Args:
            paths: List of paths to include

        Returns:
            ZIP file contents or None
        """
        try:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for path in paths:
                    if path.is_dir():
                        self._add_dir_to_zip(zf, path, path.parent)
                    else:
                        arcname = path.relative_to(self.root)
                        zf.write(path, arcname)

            return buffer.getvalue()
        except (OSError, PermissionError):
            return None

    def _add_dir_to_zip(self, zf: zipfile.ZipFile, dir_path: Path, base_path: Path):
        """Add directory contents to ZIP."""
        for item in dir_path.rglob('*'):
            if item.is_file():
                arcname = item.relative_to(base_path)
                zf.write(item, arcname)

    def get_disk_usage(self) -> Dict[str, int]:
        """
        Get disk usage information.

        Returns:
            Dictionary with total, used, free space
        """
        try:
            usage = shutil.disk_usage(self.root)
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
            }
        except OSError:
            return {"total": 0, "used": 0, "free": 0}

    def is_text_file(self, path: Path) -> bool:
        """Check if a file is a text file."""
        # Check extension first
        ext = path.suffix.lower()
        if ext in TEXT_EXTENSIONS:
            return True

        # Check common filenames
        name = path.name.lower()
        if name in ('makefile', 'dockerfile', 'cmakelists.txt', 'readme', 'license', 'changelog'):
            return True

        # Content sniffing
        try:
            with open(path, 'rb') as f:
                sample = f.read(8192)
            if not sample:
                return True
            if b'\x00' in sample:
                return False
            printable = sum(1 for b in sample if 9 <= b <= 13 or 32 <= b <= 126 or b >= 128)
            return printable / len(sample) > 0.85
        except (OSError, PermissionError):
            return False

    @staticmethod
    def _format_permissions(mode: int) -> str:
        """Format file permissions as string."""
        perms = []
        # Owner
        perms.append('r' if mode & 0o400 else '-')
        perms.append('w' if mode & 0o200 else '-')
        perms.append('x' if mode & 0o100 else '-')
        # Group
        perms.append('r' if mode & 0o040 else '-')
        perms.append('w' if mode & 0o020 else '-')
        perms.append('x' if mode & 0o010 else '-')
        # Other
        perms.append('r' if mode & 0o004 else '-')
        perms.append('w' if mode & 0o002 else '-')
        perms.append('x' if mode & 0o001 else '-')
        return ''.join(perms)



def get_icon_for_file(name: str, is_dir: bool) -> str:
    """Get emoji icon for file type."""
    if is_dir:
        return "📁"

    ext = os.path.splitext(name)[1].lower()

    icons = {
        # Code
        ".py": "🐍", ".js": "📜", ".ts": "📜", ".jsx": "⚛️", ".tsx": "⚛️",
        ".html": "🌐", ".htm": "🌐", ".css": "🎨", ".scss": "🎨", ".sass": "🎨",
        ".go": "🦫", ".rs": "🦀", ".java": "☕", ".kt": "🟣", ".swift": "🍎",
        ".c": "©️", ".cpp": "➕", ".cs": "🔷", ".rb": "💎", ".php": "🐘",
        ".vue": "💚", ".svelte": "🔥",

        # Shell
        ".sh": "⚙️", ".bash": "⚙️", ".zsh": "⚙️", ".fish": "⚙️",

        # Data
        ".json": "📋", ".yaml": "📋", ".yml": "📋", ".xml": "📋",
        ".toml": "📋", ".ini": "📋", ".conf": "📋", ".cfg": "📋",
        ".csv": "📊", ".tsv": "📊",

        # Documents
        ".md": "📝", ".markdown": "📝", ".txt": "📄", ".log": "📄",
        ".pdf": "📕", ".doc": "📘", ".docx": "📘",
        ".xls": "📗", ".xlsx": "📗", ".csv": "📊",
        ".ppt": "📙", ".pptx": "📙",

        # Images
        ".png": "🖼️", ".jpg": "🖼️", ".jpeg": "🖼️", ".gif": "🖼️",
        ".webp": "🖼️", ".svg": "🖼️", ".bmp": "🖼️", ".ico": "🖼️",

        # Video
        ".mp4": "🎬", ".webm": "🎬", ".ogg": "🎬", ".mov": "🎬",
        ".avi": "🎬", ".mkv": "🎬", ".flv": "🎬",

        # Audio
        ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵", ".aac": "🎵",
        ".ogg": "🎵", ".wma": "🎵", ".m4a": "🎵",

        # Archives
        ".zip": "🗜️", ".tar": "🗜️", ".gz": "🗜️", ".bz2": "🗜️",
        ".7z": "🗜️", ".rar": "🗜️",

        # Other
        ".env": "🔒", ".gitignore": "📋", ".dockerfile": "🐳",
        ".sql": "🗄️", ".db": "🗄️", ".sqlite": "🗄️",
    }

    return icons.get(ext, "📄")

