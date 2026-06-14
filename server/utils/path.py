"""
Path utilities.
"""

import os
import posixpath
from pathlib import Path
from typing import Optional
from urllib.parse import quote, unquote


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


def get_filename(path: str) -> str:
    """
    Get filename from path.

    Args:
        path: Path string

    Returns:
        Filename
    """
    path = normalize_path(path)
    if not path:
        return ''

    return path.split('/')[-1]


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


def encode_path_component(component: str) -> str:
    """
    Encode a path component for URLs.

    Args:
        component: Path component

    Returns:
        Encoded component
    """
    return quote(component, safe='')


def decode_path_component(component: str) -> str:
    """
    Decode a URL-encoded path component.

    Args:
        component: Encoded component

    Returns:
        Decoded component
    """
    return unquote(component)


def build_url_path(*components: str) -> str:
    """
    Build a URL path from components.

    Args:
        *components: Path components

    Returns:
        URL path
    """
    encoded = [encode_path_component(c) for c in components if c]
    return '/' + '/'.join(encoded)


def get_relative_path(path: str, base: str) -> str:
    """
    Get relative path from base.

    Args:
        path: Absolute path
        base: Base path

    Returns:
        Relative path
    """
    path = normalize_path(path)
    base = normalize_path(base)

    if not base:
        return path

    # Ensure base ends with / for prefix matching
    if not base.endswith('/'):
        base += '/'

    if path.startswith(base):
        return path[len(base):]

    # If path equals base without trailing slash
    if path == base.rstrip('/'):
        return ''

    return path


def is_subpath(path: str, parent: str) -> bool:
    """
    Check if path is a subpath of parent.

    Args:
        path: Path to check
        parent: Parent path

    Returns:
        True if path is under parent
    """
    path = normalize_path(path)
    parent = normalize_path(parent)

    if not parent:
        return True

    # Ensure parent ends with / for prefix matching
    if not parent.endswith('/'):
        parent += '/'

    return path.startswith(parent) or path == parent.rstrip('/')


def split_path(path: str) -> list:
    """
    Split path into components.

    Args:
        path: Path to split

    Returns:
        List of path components
    """
    path = normalize_path(path)
    if not path:
        return []

    return path.split('/')


def common_path(paths: list) -> str:
    """
    Find common path prefix.

    Args:
        paths: List of paths

    Returns:
        Common prefix
    """
    if not paths:
        return ''

    # Split all paths
    split_paths = [split_path(p) for p in paths]

    # Find common prefix
    common = []
    for components in zip(*split_paths):
        if len(set(components)) == 1:
            common.append(components[0])
        else:
            break

    return '/'.join(common)
