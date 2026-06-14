"""
Formatting utilities.
"""

import os
from datetime import datetime


def format_size(size: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024:
            if unit == 'B':
                return f"{size} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_time(timestamp: float, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format timestamp to human-readable string.

    Args:
        timestamp: Unix timestamp
        fmt: strftime format string

    Returns:
        Formatted time string
    """
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime(fmt)
    except (ValueError, OSError):
        return "Unknown"

def format_permissions(mode: int) -> str:
    """
    Format file permissions as Unix-style string.

    Args:
        mode: File mode (from os.stat)

    Returns:
        Permissions string (e.g., "rwxr-xr-x")
    """
    perms = []

    # File type
    import stat
    if stat.S_ISDIR(mode):
        perms.append('d')
    elif stat.S_ISLNK(mode):
        perms.append('l')
    else:
        perms.append('-')

    # Owner permissions
    perms.append('r' if mode & 0o400 else '-')
    perms.append('w' if mode & 0o200 else '-')
    perms.append('x' if mode & 0o100 else '-')

    # Group permissions
    perms.append('r' if mode & 0o040 else '-')
    perms.append('w' if mode & 0o020 else '-')
    perms.append('x' if mode & 0o010 else '-')

    # Other permissions
    perms.append('r' if mode & 0o004 else '-')
    perms.append('w' if mode & 0o002 else '-')
    perms.append('x' if mode & 0o001 else '-')

    return ''.join(perms)


def escape_html(text: str) -> str:
    """
    Escape HTML special characters.

    Args:
        text: Text to escape

    Returns:
        Escaped text
    """
    return (
        text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )

