"""
File preview template.
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
<div class="toolbar">
    <div class="container">
        <div class="toolbar-row">
            <a href="/?p={quote(_get_parent_path(file_path))}" class="btn btn-outline btn-sm">← Back</a>
            <span class="breadcrumb">
                <a href="/">/</a>
                {_build_path_breadcrumb(file_path)}
            </span>
            <div style="flex: 1;"></div>
            <a href="/raw?p={encoded_path}" class="btn btn-sm btn-outline">⬇️ Download</a>
            {'<a href="/?p=' + encoded_path + '&edit=1" class="btn btn-sm btn-outline">✏️ Edit</a>' if is_text else ''}
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌓</button>
        </div>
    </div>
</div>

<div class="container">
    <div class="preview-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
                <h2 style="margin: 0; font-size: 20px;">{file_name}</h2>
                <div style="color: var(--text-secondary); font-size: 12px; margin-top: 4px;">
                    {mime_type or 'Unknown type'} • {size_str}
                </div>
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
        <div style="padding: 32px; background: var(--bg-secondary); border-radius: var(--radius); text-align: center;">
            <div style="font-size: 48px; margin-bottom: 16px;">🎵</div>
            <audio controls style="width: 100%; max-width: 500px;">
                <source src="/raw?p={encoded_path}" type="{mime_type}">
                Your browser does not support the audio tag.
            </audio>
        </div>"""

    # PDF preview
    if ext == '.pdf':
        return f"""
        <div style="background: var(--bg-secondary); border-radius: var(--radius); overflow: hidden;">
            <iframe src="/raw?p={encoded_path}" style="width: 100%; height: 80vh; border: none;"></iframe>
        </div>"""

    # Markdown preview
    if ext in ('.md', '.markdown') and content:
        # Simple markdown rendering (basic formatting)
        rendered = _simple_markdown(content)
        return f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <div>
                <h3 style="margin-bottom: 8px; color: var(--text-secondary);">Source</h3>
                <pre class="preview-code" style="max-height: 80vh; overflow-y: auto;">{_escape_html(content)}</pre>
            </div>
            <div>
                <h3 style="margin-bottom: 8px; color: var(--text-secondary);">Preview</h3>
                <div class="preview-code markdown-preview" style="max-height: 80vh; overflow-y: auto;">
                    {rendered}
                </div>
            </div>
        </div>"""

    # Text file preview
    if is_text and content:
        # Add syntax highlighting class based on extension
        lang_class = f"language-{_get_highlight_lang(ext)}" if ext else ""
        return f"""
        <div style="position: relative;">
            <button class="btn btn-sm btn-outline" style="position: absolute; top: 8px; right: 8px;"
                    onclick="copyContent()">
                📋 Copy
            </button>
            <pre class="preview-code {lang_class}" id="code-content"
                 style="max-height: 80vh; overflow-y: auto;">{_escape_html(content)}</pre>
        </div>
        <script>
        function copyContent() {{
            const content = document.getElementById('code-content').textContent;
            navigator.clipboard.writeText(content).then(() => {{
                showToast('Content copied to clipboard', 'success');
            }});
        }}
        </script>"""

    # Generic file info
    return f"""
    <div style="padding: 32px; background: var(--bg-secondary); border-radius: var(--radius); text-align: center;">
        <div style="font-size: 48px; margin-bottom: 16px;">📄</div>
        <p style="color: var(--text-secondary); margin-bottom: 16px;">
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


def _get_highlight_lang(ext: str) -> str:
    """Get language for syntax highlighting."""
    lang_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".xml": "xml",
        ".md": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".sql": "sql",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
    }
    return lang_map.get(ext, "plaintext")


def _simple_markdown(text: str) -> str:
    """Simple markdown rendering."""
    import re

    # Escape HTML
    text = _escape_html(text)

    # Headers
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)

    # Bold and italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # Links
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)

    # Code blocks
    text = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code class="language-\1">\2</code></pre>', text, flags=re.DOTALL)

    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

    # Line breaks
    text = text.replace('\n', '<br>')

    return text
