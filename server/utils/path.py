"""
Path utilities.
"""

from pathlib import Path
from urllib.parse import quote, unquote
from .format import escape_html

def normalize_path(path: str) -> str:
    """
    Normalize a path string.

    Args:
        path: Path string to normalize

    Returns:
        Normalized path
    """
    # Decode URL encoding
    path = unquote(path)

    # Remove leading/trailing slashes
    path = path.strip('/')

    # Normalize separators
    path = path.replace('\\', '/')

    # Remove double slashes
    while '//' in path:
        path = path.replace('//', '/')

    # Remove . and ..
    parts = []
    for part in path.split('/'):
        if part == '.':
            continue
        elif part == '..':
            if parts:
                parts.pop()
        elif part:
            parts.append(part)

    return '/'.join(parts)


def join_paths(*paths: str) -> str:
    """
    Join path components.

    Args:
        *paths: Path components to join

    Returns:
        Joined path
    """
    # Filter empty strings
    paths = [p for p in paths if p]

    if not paths:
        return ''

    # Join with /
    result = '/'.join(paths)

    # Normalize
    return normalize_path(result)


def get_parent_path(path: str) -> str:
    """
    Get parent directory path.

    Args:
        path: Path string

    Returns:
        Parent path
    """
    path = normalize_path(path)
    if not path:
        return ''

    parts = path.split('/')
    if len(parts) <= 1:
        return ''

    return '/'.join(parts[:-1])


def build_path_breadcrumb(path: str) -> str:
    """
    Build breadcrumb HTML for a file path (used in editor/preview).
    """
    if not path:
        return ""
    parts = path.strip('/').split('/')
    html = ""
    current = ""
    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            html += f'<span class="separator">/</span><span class="current">{escape_html(part)}</span>'
        else:
            current += "/" + part if current else part
            encoded = quote(current)
            html += f'<span class="separator">/</span><a href="/?p={encoded}">{escape_html(part)}</a>'
    return html


def build_breadcrumb(path: str) -> str:
    """
    Build breadcrumb HTML for a directory path (used in listing).
    """
    if not path:
        return '<span class="current">/</span>'
    parts = path.strip('/').split('/')
    html = '<a href="/">/</a>'
    current = ""
    for i, part in enumerate(parts):
        current += "/" + part if current else part
        encoded = quote(current)
        if i == len(parts) - 1:
            html += f'<span class="separator">/</span><span class="current">{escape_html(part)}</span>'
        else:
            html += f'<span class="separator">/</span><a href="/?p={encoded}">{escape_html(part)}</a>'
    return html


def get_extension(filename: str) -> str:
    """
    Get file extension.

    Args:
        filename: Filename

    Returns:
        Extension with dot (e.g., '.txt')
    """
    if '.' in filename:
        return '.' + filename.rsplit('.', 1)[1].lower()
    return ''


def is_safe_path(path: str) -> bool:
    """
    Check if a path is safe (no traversal).

    Args:
        path: Path to check

    Returns:
        True if path is safe
    """
    # Decode URL encoding
    path = unquote(path)

    # Check for null bytes
    if '\x00' in path:
        return False

    # Check for ..
    parts = path.split('/')
    for part in parts:
        if part == '..':
            return False

    return True
