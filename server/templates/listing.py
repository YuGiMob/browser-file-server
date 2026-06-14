"""
Directory listing template.
"""

from typing import List, Optional
from urllib.parse import quote

from ..storage import FileInfo, format_size, format_time, get_icon_for_file


def render_listing(
    files: List[FileInfo],
    current_path: str,
    search_query: str = "",
    sort_by: str = "name",
    show_hidden: bool = False,
    flash_message: str = "",
    flash_type: str = "success",
    page: int = 1,
    total_pages: int = 1,
    features: Optional[dict] = None,
) -> str:
    """
    Render directory listing HTML.

    Args:
        files: List of file info objects
        current_path: Current directory path
        search_query: Search query
        sort_by: Current sort field
        show_hidden: Whether hidden files are shown
        flash_message: Flash message to display
        flash_type: Flash message type
        page: Current page number
        total_pages: Total number of pages
        features: Feature flags

    Returns:
        HTML string
    """
    features = features or {}
    encoded_path = quote(current_path)

    # Build breadcrumb
    breadcrumb = _build_breadcrumb(current_path)

    # Build flash message
    flash_html = ""
    if flash_message:
        flash_html = f'<div class="flash flash-{flash_type}">{flash_message}</div>'

    # Build file list
    file_items = []
    for file_info in files:
        file_items.append(_render_file_item(file_info, current_path, features))

    # Build sort options
    sort_options = _build_sort_options(sort_by, current_path)

    # Build pagination
    pagination_html = _build_pagination(page, total_pages, current_path, search_query)

    # Build feature-specific elements
    upload_html = ""
    if features.get("upload", True):
        upload_html = f"""
        <div class="upload-zone" id="upload-zone">
            <div class="upload-zone-text">
                Drag and drop files here or click to select
            </div>
            <form method="post" action="/upload" enctype="multipart/form-data" id="upload-form">
                <input type="hidden" name="p" value="{current_path}">
                <input type="file" name="f" multiple id="file-input" style="display: none;">
                <button type="button" class="btn" onclick="document.getElementById('file-input').click()">
                    📁 Select Files
                </button>
                <button type="submit" class="btn btn-success" style="margin-left: 8px;">
                    ⬆️ Upload
                </button>
            </form>
        </div>"""

    mkdir_html = ""
    if features.get("mkdir", True):
        mkdir_html = f"""
        <form method="post" action="/mkdir" class="toolbar-row">
            <input type="hidden" name="p" value="{current_path}">
            <input type="text" name="name" placeholder="New folder name" required>
            <button type="submit" class="btn btn-sm">📁 New Folder</button>
        </form>"""

    search_html = ""
    if features.get("search", True):
        search_html = f"""
        <form method="get" action="/search" class="search-form">
            <input type="hidden" name="p" value="{current_path}">
            <input type="search" name="q" value="{search_query}" placeholder="Search files..." class="search-input">
            <button type="submit" class="btn btn-sm">🔍 Search</button>
        </form>"""

    # Build page
    html = f"""
<div class="toolbar">
    <div class="container">
        <div class="toolbar-content">
            <div class="toolbar-row">
                <a href="/?p={quote(_get_parent_path(current_path))}" class="btn btn-outline btn-sm">⬆️ Up</a>
                <div class="breadcrumb">{breadcrumb}</div>
                <div style="flex: 1;"></div>
                {search_html}
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌓</button>
            </div>
            <div class="toolbar-row">
                {mkdir_html}
                {sort_options}
                <label style="display: flex; align-items: center; gap: 4px; cursor: pointer;">
                    <input type="checkbox" id="select-all" onchange="selectAll(this.checked)">
                    <span style="font-size: 12px;">Select all</span>
                </label>
                <label style="display: flex; align-items: center; gap: 4px; cursor: pointer;">
                    <input type="checkbox" {'checked' if show_hidden else ''} 
                           onchange="toggleHidden(this.checked)">
                    <span style="font-size: 12px;">Show hidden</span>
                </label>
            </div>
        </div>
    </div>
</div>

<div class="container">
    {flash_html}
    
    {upload_html}
    
    <div style="display: flex; justify-content: space-between; align-items: center; margin: 16px 0; flex-wrap: wrap; gap: 8px;">
        <div class="filter-bar" style="margin: 0;">
            <button class="filter-btn active" data-filter="all">All</button>
            <button class="filter-btn" data-filter="folder">📁 Folders</button>
            <button class="filter-btn" data-filter="text">📄 Documents</button>
            <button class="filter-btn" data-filter="image">🖼️ Images</button>
            <button class="filter-btn" data-filter="video">🎬 Videos</button>
            <button class="filter-btn" data-filter="audio">🎵 Audio</button>
        </div>
        <div id="batch-actions" style="display: none;">
            <button class="btn btn-sm btn-success" onclick="downloadSelected()">📦 Download Selected as ZIP</button>
            <span id="selected-count" style="margin-left: 8px; color: var(--text-secondary); font-size: 12px;"></span>
        </div>
    </div>
    
    <ul class="file-list" id="file-list">
        {''.join(file_items) if file_items else '<li class="file-item"><div class="file-info"><span class="file-name" style="color: var(--text-secondary);">No files found</span></div></li>'}
    </ul>
    
    {pagination_html}
</div>

<script>
// File input change handler
const fileInput = document.getElementById('file-input');
if (fileInput) {{
    fileInput.addEventListener('change', function() {{
        if (this.files.length > 0) {{
            document.getElementById('upload-form').submit();
        }}
    }});
}}

// Filter functionality
document.querySelectorAll('.filter-btn').forEach(btn => {{
    btn.addEventListener('click', function() {{
        // Update active state
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        
        const filter = this.dataset.filter;
        const items = document.querySelectorAll('.file-item');
        
        items.forEach(item => {{
            if (filter === 'all') {{
                item.style.display = '';
            }} else {{
                const category = item.dataset.category;
                item.style.display = (category === filter) ? '' : 'none';
            }}
        }});
    }});
}});

// Toggle hidden files
function toggleHidden(show) {{
    const url = new URL(window.location);
    url.searchParams.set('hidden', show ? '1' : '0');
    window.location.href = url.toString();
}}

// Confirm delete
function confirmDelete(name) {{
    return confirm(`Are you sure you want to delete "${{name}}"?`);
}}
</script>
"""

    return html


def _build_breadcrumb(path: str) -> str:
    """Build breadcrumb navigation."""
    if not path:
        return '<span class="current">/</span>'

    parts = path.strip('/').split('/')
    html = '<a href="/">/</a>'

    current = ""
    for i, part in enumerate(parts):
        current += "/" + part if current else part
        encoded = quote(current)
        if i == len(parts) - 1:
            html += f'<span class="separator">/</span><span class="current">{part}</span>'
        else:
            html += f'<span class="separator">/</span><a href="/?p={encoded}">{part}</a>'

    return html


def _get_parent_path(path: str) -> str:
    """Get parent directory path."""
    if not path:
        return ""
    parts = path.rstrip('/').split('/')
    return '/'.join(parts[:-1])


def _render_file_item(file_info: FileInfo, current_path: str, features: dict) -> str:
    """Render a single file item."""
    icon = get_icon_for_file(file_info.name, file_info.is_dir)
    encoded_path = quote(file_info.path)
    name_class = "file-name is-dir" if file_info.is_dir else "file-name"

    # Build link
    if file_info.is_dir:
        link = f'<a href="/?p={encoded_path}">{file_info.name}/</a>'
    elif file_info.is_text and features.get("edit", True):
        link = f'<a href="/?p={encoded_path}&edit=1">{file_info.name}</a>'
    else:
        link = f'<a href="/raw?p={encoded_path}">{file_info.name}</a>'

    # Build metadata
    meta_parts = []
    if not file_info.is_dir:
        meta_parts.append(f'<span>{format_size(file_info.size)}</span>')
    meta_parts.append(f'<span>{file_info.modified_str}</span>')
    meta_parts.append(f'<span>{file_info.permissions}</span>')
    meta_html = '<div class="file-meta">' + ''.join(meta_parts) + '</div>'

    # Build actions
    actions = []
    if file_info.is_dir:
        actions.append(f'<a href="/download?p={encoded_path}" class="btn btn-sm btn-outline" title="Download as ZIP">📦 ZIP</a>')
        actions.append(f'<a href="/?p={encoded_path}" class="btn btn-sm btn-outline">Open</a>')
    else:
        if file_info.is_text and features.get("edit", True):
            actions.append(f'<a href="/?p={encoded_path}&edit=1" class="btn btn-sm btn-outline">Edit</a>')
        actions.append(f'<a href="/raw?p={encoded_path}" class="btn btn-sm btn-outline">Download</a>')

    if features.get("delete", True):
        actions.append(
            f'<a href="/delete?p={encoded_path}" class="btn btn-sm btn-danger" '
            f'onclick="return confirmDelete(\'{file_info.name}\')">Delete</a>'
        )

    actions_html = '<div class="file-actions">' + ''.join(actions) + '</div>'

    # Get category for filtering
    category = _get_category(file_info)

    # Build checkbox for multi-select
    checkbox = f'<input type="checkbox" class="file-checkbox" data-path="{file_info.path}" onchange="updateSelected()">'
    
    return f"""
    <li class="file-item" data-category="{category}">
        {checkbox}
        <div class="file-icon">{icon}</div>
        <div class="file-info">
            <div class="{name_class}">{link}</div>
            {meta_html}
        </div>
        {actions_html}
    </li>"""


def _get_category(file_info: FileInfo) -> str:
    """Get file category for filtering."""
    if file_info.is_dir:
        return "folder"

    ext = file_info.name.rsplit('.', 1)[-1].lower() if '.' in file_info.name else ""

    image_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico'}
    video_exts = {'mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv', 'flv'}
    audio_exts = {'mp3', 'wav', 'ogg', 'flac', 'aac', 'wma', 'm4a'}

    if ext in image_exts:
        return "image"
    if ext in video_exts:
        return "video"
    if ext in audio_exts:
        return "audio"

    return "text"


def _build_sort_options(sort_by: str, current_path: str) -> str:
    """Build sort options HTML."""
    encoded_path = quote(current_path)
    options = [
        ("name", "Name"),
        ("size", "Size"),
        ("modified", "Modified"),
    ]

    buttons = []
    for value, label in options:
        active = "active" if sort_by == value else ""
        buttons.append(
            f'<a href="/?p={encoded_path}&sort={value}" '
            f'class="filter-btn {active}">{label}</a>'
        )

    return f'<div class="toolbar-row">Sort: {"".join(buttons)}</div>'


def _build_pagination(page: int, total_pages: int, current_path: str, search_query: str) -> str:
    """Build pagination HTML."""
    if total_pages <= 1:
        return ""

    encoded_path = quote(current_path)
    encoded_query = quote(search_query) if search_query else ""

    buttons = []

    # Previous button
    if page > 1:
        buttons.append(
            f'<a href="/?p={encoded_path}&page={page-1}&q={encoded_query}" '
            f'class="btn btn-sm btn-outline">← Previous</a>'
        )

    # Page numbers
    start = max(1, page - 2)
    end = min(total_pages, page + 2)

    if start > 1:
        buttons.append(
            f'<a href="/?p={encoded_path}&page=1&q={encoded_query}" '
            f'class="btn btn-sm btn-outline">1</a>'
        )
        if start > 2:
            buttons.append('<span style="color: var(--text-muted);">...</span>')

    for p in range(start, end + 1):
        if p == page:
            buttons.append(f'<span class="btn btn-sm">{p}</span>')
        else:
            buttons.append(
                f'<a href="/?p={encoded_path}&page={p}&q={encoded_query}" '
                f'class="btn btn-sm btn-outline">{p}</a>'
            )

    if end < total_pages:
        if end < total_pages - 1:
            buttons.append('<span style="color: var(--text-muted);">...</span>')
        buttons.append(
            f'<a href="/?p={encoded_path}&page={total_pages}&q={encoded_query}" '
            f'class="btn btn-sm btn-outline">{total_pages}</a>'
        )

    # Next button
    if page < total_pages:
        buttons.append(
            f'<a href="/?p={encoded_path}&page={page+1}&q={encoded_query}" '
            f'class="btn btn-sm btn-outline">Next →</a>'
        )

    return f'<div style="display: flex; justify-content: center; gap: 8px; margin: 24px 0;">{"".join(buttons)}</div>'
