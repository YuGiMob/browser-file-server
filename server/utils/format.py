"""
Formatting utilities.
"""

import os
from datetime import datetime
from typing import Optional


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


def format_relative_time(timestamp: float) -> str:
    """
    Format timestamp as relative time (e.g., "2 hours ago").

    Args:
        timestamp: Unix timestamp

    Returns:
        Relative time string
    """
    try:
        now = datetime.now()
        dt = datetime.fromtimestamp(timestamp)
        diff = now - dt

        seconds = diff.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif seconds < 31536000:
            months = int(seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(seconds / 31536000)
            return f"{years} year{'s' if years != 1 else ''} ago"
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
    if os.path.S_ISDIR(mode):
        perms.append('d')
    elif os.path.S_ISLNK(mode):
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


def format_number(n: int) -> str:
    """
    Format number with thousand separators.

    Args:
        n: Number to format

    Returns:
        Formatted number string
    """
    return f"{n:,}"


def truncate_path(path: str, max_length: int = 50) -> str:
    """
    Truncate path to maximum length.

    Args:
        path: Path to truncate
        max_length: Maximum length

    Returns:
        Truncated path
    """
    if len(path) <= max_length:
        return path

    # Try to keep the filename
    parts = path.split('/')
    if len(parts) > 1:
        filename = parts[-1]
        dir_path = '/'.join(parts[:-1])

        # Calculate how much of the directory path we can show
        available = max_length - len(filename) - 4  # 4 for "/.../"
        if available > 0:
            return f"{dir_path[:available]}/.../{filename}"

    # Fallback: truncate from the beginning
    return f"...{path[-(max_length-3):]}"


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


def unescape_html(text: str) -> str:
    """
    Unescape HTML special characters.

    Args:
        text: Text to unescape

    Returns:
        Unescaped text
    """
    return (
        text
        .replace('&amp;', '&')
        .replace('&lt;', '<')
        .replace('&gt;', '>')
        .replace('&quot;', '"')
        .replace('&#39;', "'")
    )
