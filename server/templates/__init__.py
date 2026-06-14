"""
HTML template generation for the file server UI.

Provides:
- Base HTML structure
- Directory listing
- File editor
- File preview
- Error pages
"""

from .base import get_base_html, get_head, get_footer
from .listing import render_listing
from .editor import render_editor
from .preview import render_preview
from .error import render_error

__all__ = [
    'get_base_html',
    'get_head',
    'get_footer',
    'render_listing',
    'render_editor',
    'render_preview',
    'render_error',
]
