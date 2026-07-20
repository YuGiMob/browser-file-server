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
    import stat
    perms = ['d' if stat.S_ISDIR(mode) else 'l' if stat.S_ISLNK(mode) else '-']
    for i, c in enumerate('rwxrwxrwx'):
        perms.append(c if mode & (1 << (8 - i)) else '-')
    return ''.join(perms)

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

