"""
File preview template with professional mobile-app design.
"""

from urllib.parse import quote
from typing import Optional
import os


def render_preview(
    file_path: str,
    file_name: str,
    mime_type: Optional[str],
    file_size: int,
    content: Optional[str] = None,
    is_text: bool = False,
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

    Returns:
        HTML string
    """
    encoded_path = quote(file_path)
    ext = os.path.splitext(file_name)[1].lower()

    # Determine preview type
    preview_content = _get_preview_content(
        file_path, file_name, mime_type, ext, content, is_text
    )

    # Format file size
    size_str = _format_size(file_size)

    html = f"""
<div class="header">
    <div class="header-content">
        <div class="header-top">
            <a href="/?p={quote(_get_parent_path(file_path))}" class="btn-icon">←</a>
            <span class="header-title">{file_name}</span>
            <div class="header-actions">
                <a href="/raw?p={encoded_path}" class="btn-icon" title="Download">⬇️</a>
                {'<a href="/?p=' + encoded_path + '&edit=1" class="btn-icon" title="Edit">✏️</a>' if is_text else ''}
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌓</button>
            </div>
        </div>
        <div class="breadcrumb">
            <a href="/">/</a>
            {_build_path_breadcrumb(file_path)}
        </div>
    </div>
</div>

<div class="container">
    <div class="preview-container">
        <div class="preview-header">
            <div>
                <div class="preview-title">{file_name}</div>
                <div class="preview-subtitle">{mime_type or 'Unknown type'} · {size_str}</div>
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

    # Image preview
    if ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico'):
        return f"""
        <div style="text-align: center;">
            <img src="/raw?p={encoded_path}" alt="{file_name}" class="preview-image"
                 style="max-width: 100%; max-height: 80vh; border-radius: var(--radius);">
        </div>"""

    # Video preview
    if ext in ('.mp4', '.webm', '.ogg', '.mov'):
        return f"""
        <div style="text-align: center;">
            <video controls class="preview-video" style="max-width: 100%; border-radius: var(--radius);">
                <source src="/raw?p={encoded_path}" type="{mime_type}">
                Your browser does not support the video tag.
            </video>
        </div>"""

    # Audio preview
    if ext in ('.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'):
        return f"""
        <div style="padding: 32px; background: var(--bg-card); border-radius: var(--radius); text-align: center;">
            <div style="font-size: 64px; margin-bottom: 16px;">🎵</div>
            <audio controls style="width: 100%; max-width: 500px;">
                <source src="/raw?p={encoded_path}" type="{mime_type}">
                Your browser does not support the audio tag.
            </audio>
        </div>"""

    # PDF preview
    if ext == '.pdf':
        return f"""
        <div style="background: var(--bg-card); border-radius: var(--radius); overflow: hidden;">
            <iframe src="/raw?p={encoded_path}" style="width: 100%; height: 80vh; border: none;"></iframe>
        </div>"""

    # Text file preview
    if is_text and content:
        return f"""
        <div style="position: relative;">
            <button class="btn btn-sm btn-ghost" style="position: absolute; top: 8px; right: 8px;"
                    onclick="copyContent()">
                📋 Copy
            </button>
            <pre class="preview-code" id="code-content">{_escape_html(content)}</pre>
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
        <a href="/raw?p={encoded_path}" class="btn">
            ⬇️ Download File
        </a>
    </div>"""


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )


def _get_parent_path(path: str) -> str:
    """Get parent directory path."""
    if not path:
        return ""
    parts = path.rstrip('/').split('/')
    return '/'.join(parts[:-1])


def _build_path_breadcrumb(path: str) -> str:
    """Build breadcrumb for file path."""
    if not path:
        return ""

    parts = path.strip('/').split('/')
    html = ""
    current = ""

    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            # Last part (filename) - not a link
            html += f'<span class="separator">/</span><span class="current">{part}</span>'
        else:
            current += "/" + part if current else part
            from urllib.parse import quote as url_quote
            encoded = url_quote(current)
            html += f'<span class="separator">/</span><a href="/?p={encoded}">{part}</a>'

    return html


def _format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024:
            if unit == 'B':
                return f"{size} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
