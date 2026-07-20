"""
File preview template with professional mobile-app design.
"""

from urllib.parse import quote
from typing import Optional
import os
from ..utils.format import escape_html, format_size
from ..utils.path import get_parent_path, build_path_breadcrumb
from ..utils.mime import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS
from .. import RAW
def render_preview(
    file_path: str,
    file_name: str,
    mime_type: Optional[str],
    file_size: int,
    content: Optional[str] = None,
    is_text: bool = False,
    csrf_token: str = "",
) -> str:
    """
    Render file preview HTML.

    Args:
        file_path: Path to the file
        file_name: File name
        mime_type: MIME type of the file
        file_size: File size in bytes
        content: Text content (for text files)
        is_text: Whether the file is a text file
        csrf_token: CSRF token for forms

    Returns:
        HTML string
    """
    encoded_path = quote(file_path)
    ext = os.path.splitext(file_name)[1].lower()
    safe_file_name = escape_html(file_name)

    # Determine preview type
    preview_content = _get_preview_content(
        file_path, file_name, mime_type, ext, content, is_text
    )

    # Format file size
    size_str = format_size(file_size)

    html = f"""
<div class="header">
    <div class="header-content">
        <div class="header-top">
            <a href="/?p={quote(get_parent_path(file_path))}" class="btn-icon">←</a>
            <span class="header-title">{safe_file_name}</span>
            <div class="header-actions">
                <a href="{RAW}?p={encoded_path}" class="btn-icon" title="Download">⬇️</a>
                {'<a href="/?p=' + encoded_path + '&edit=1" class="btn-icon" title="Edit">✏️</a>' if is_text else ''}
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌓</button>
            </div>
        </div>
        <div class="breadcrumb">
            <a href="/">/</a>
            {build_path_breadcrumb(file_path)}
        </div>
    </div>
</div>

<div class="container">
    <div class="preview-container">
        <div class="preview-header">
            <div>
                <div class="preview-title">{safe_file_name}</div>
                <div class="preview-subtitle">{escape_html(mime_type or 'Unknown type')} · {size_str}</div>
            </div>
        </div>
        
        {preview_content}
    </div>
</div>

<script>
// Keyboard shortcuts
document.addEventListener('keydown', function(e) {{
    // Escape to go back
    if (e.key === 'Escape') {{
        window.history.back();
    }}
    
    // E to edit
    if (e.key === 'e' && !e.ctrlKey && !e.metaKey && document.activeElement.tagName !== 'INPUT') {{
        const editLink = document.querySelector('a[href*="edit=1"]');
        if (editLink) {{
            window.location.href = editLink.href;
        }}
    }}
}});
</script>
"""

    return html


def _get_preview_content(
    file_path: str,
    file_name: str,
    mime_type: Optional[str],
    ext: str,
    content: Optional[str],
    is_text: bool,
) -> str:
    """Get preview content based on file type."""
    encoded_path = quote(file_path)
    safe_file_name = escape_html(file_name)

    # Image preview
    if ext in IMAGE_EXTENSIONS:
        return f"""
        <div style="text-align: center;">
            <img src="{RAW}?p={encoded_path}" alt="{safe_file_name}" class="preview-image"
                 style="max-width: 100%; max-height: 80vh; border-radius: var(--radius);">
        </div>"""

    # Video preview
    if ext in VIDEO_EXTENSIONS:
        return f"""
        <div style="text-align: center;">
            <video controls class="preview-video" style="max-width: 100%; border-radius: var(--radius);">
                <source src="{RAW}?p={encoded_path}" type="{escape_html(mime_type or '')}">
                Your browser does not support the video tag.
            </video>
        </div>"""

    # Audio preview
    if ext in AUDIO_EXTENSIONS:
        return f"""
        <div style="padding: 32px; background: var(--bg-card); border-radius: var(--radius); text-align: center;">
            <div style="font-size: 64px; margin-bottom: 16px;">🎵</div>
            <audio controls style="width: 100%; max-width: 500px;">
                <source src="{RAW}?p={encoded_path}" type="{escape_html(mime_type or '')}">
                Your browser does not support the audio tag.
            </audio>
        </div>"""

    # PDF preview
    if ext == '.pdf':
        return f"""
        <div style="background: var(--bg-card); border-radius: var(--radius); overflow: hidden;">
            <iframe src="{RAW}?p={encoded_path}" style="width: 100%; height: 80vh; border: none;"></iframe>
        </div>"""

    # Text file preview
    if is_text and content:
        return f"""
        <div style="position: relative;">
            <button class="btn btn-sm btn-ghost" style="position: absolute; top: 8px; right: 8px;"
                    onclick="copyContent()">
                📋 Copy
            </button>
            <pre class="preview-code" id="code-content">{escape_html(content)}</pre>
        </div>
        <script>
        function copyContent() {{
            const content = document.getElementById('code-content').textContent;
            navigator.clipboard.writeText(content).then(() => {{
                showToast('Copied to clipboard', 'success');
            }});
        }}
        </script>"""

    # Generic file info
    return f"""
    <div style="padding: 48px 32px; background: var(--bg-card); border-radius: var(--radius); text-align: center;">
        <div style="font-size: 64px; margin-bottom: 16px;">📄</div>
        <p style="color: var(--text-secondary); margin-bottom: 24px;">
            Preview not available for this file type
        </p>
        <a href="{RAW}?p={encoded_path}" class="btn">
            ⬇️ Download File
        </a>
    </div>"""


