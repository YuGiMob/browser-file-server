"""
Directory listing template with professional mobile-app design.
"""

from typing import List, Optional
from urllib.parse import quote

from ..storage import FileInfo, format_size, get_icon_for_file
from ..utils.format import escape_html
from ..utils.path import get_parent_path, build_path_breadcrumb
from .. import UPLOAD, SEARCH, DOWNLOAD, RAW, DELETE, DOWNLOAD_SELECTED
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
    csrf_token: str = "",
    features: Optional[dict] = None,
) -> str:
    """
    Render directory listing HTML.
    """
    features = features or {}
    encoded_path = quote(current_path)
    breadcrumb = build_path_breadcrumb(current_path, with_root=True)
    
    flash_html = ""
    if flash_message:
        flash_html = f'<div class="flash flash-{flash_type}">{flash_message}</div>'
    
    file_items = []
    for file_info in files:
        file_items.append(_render_file_item(file_info, current_path, features, csrf_token, search_query))
    
    upload_html = ""
    if features.get("upload", True):
        upload_html = f'''
        <div class="upload-zone" id="upload-zone">
            <div class="upload-zone-icon">\U0001f4c1</div>
            <div class="upload-zone-text">
                <strong>Tap to upload</strong> or drag files here
            </div>
            <form method="post" action="{UPLOAD}" enctype="multipart/form-data" id="upload-form" style="margin-top: 16px;">
                <input type="hidden" name="p" value="{escape_html(current_path)}">
                <input type="hidden" name="_csrf" value="{escape_html(csrf_token)}">
                <input type="file" name="f" multiple id="file-input" style="display: none;" accept="*/*">
                <button type="button" class="btn btn-ghost" onclick="document.getElementById('file-input').click()">
                    Choose Files
                </button>
            </form>
        </div>'''
    
    # Build search bar conditionally
    search_html = ""
    if features.get("search", True):
        search_html = f'''
    <div class="search-bar">
        <form method="get" action="{SEARCH}" class="search-input-wrapper">
            <input type="hidden" name="p" value="{escape_html(current_path)}">
            <span class="search-icon">\U0001f50d</span>
            <input type="search" name="q" value="{escape_html(search_query)}" placeholder="Search" class="search-input">
        </form>
    </div>'''
    
    empty_html = ""
    if not file_items:
        empty_html = '<div class="empty-state"><div class="empty-state-icon">\U0001f4c2</div><div class="empty-state-title">No Files</div><div class="empty-state-text">This folder is empty. Upload files to get started.</div></div>'
    
    file_list_html = "".join(file_items)
    
    html = f"""
<div class="header">
    <div class="header-content">
        <div class="header-top">
            <a href="/?p={quote(get_parent_path(current_path))}" class="btn-icon">⬆️</a>
            <span class="header-title">{escape_html(_get_display_name(current_path))}</span>
            <div class="header-actions">
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">\U0001f313</button>
            </div>
        </div>
        <div class="breadcrumb">{breadcrumb}</div>
    </div>
    {search_html}
    <div class="toolbar">
        <div class="segmented-control">
            <a href="/?p={encoded_path}&sort=name" class="segmented-btn {'active' if sort_by == 'name' else ''}">Name</a>
            <a href="/?p={encoded_path}&sort=size" class="segmented-btn {'active' if sort_by == 'size' else ''}">Size</a>
            <a href="/?p={encoded_path}&sort=modified" class="segmented-btn {'active' if sort_by == 'modified' else ''}">Date</a>
        </div>
        <div class="toolbar-spacer"></div>
        <label class="checkbox-wrapper {'checked' if show_hidden else ''}" onclick="toggleHidden({str(not show_hidden).lower()})">
            <div class="checkbox-indicator"></div>
            <span class="checkbox-label">Hidden</span>
        </label>
    </div>
</div>

<div class="container">
    {flash_html}
    {upload_html}
    {empty_html}
    {file_list_html}
    {_build_pagination(page, total_pages, current_path, search_query)}
</div>

<div id="batch-bar" class="batch-bar">
    <span id="batch-count" class="batch-info">0 selected</span>
    <div class="batch-actions">
        <button class="btn btn-sm btn-ghost" onclick="downloadSelected()">\U0001f4e6 ZIP</button>
        <button class="btn btn-sm btn-danger" onclick="deleteSelected()">\U0001f5d1\ufe0f Delete</button>
        <button class="btn btn-sm btn-ghost" onclick="clearSelection()">Clear</button>
    </div>
</div>

<script>
let selectedFiles = new Set();

function clearSelection() {{
    selectedFiles.clear();
    updateBatchBar();
    
    document.querySelectorAll('.file-checkbox').forEach(cb => {{
        cb.classList.remove('checked');
    }});
    
    document.querySelectorAll('.file-item').forEach(item => {{
        item.classList.remove('selected');
    }});
}}

function toggleFileSelect(path, element) {{
    if (selectedFiles.has(path)) {{
        selectedFiles.delete(path);
        element.classList.remove('checked');
        element.closest('.file-item').classList.remove('selected');
    }} else {{
        selectedFiles.add(path);
        element.classList.add('checked');
        element.closest('.file-item').classList.add('selected');
    }}
    
    updateBatchBar();
}}

function updateBatchBar() {{
    const batchBar = document.getElementById('batch-bar');
    const batchCount = document.getElementById('batch-count');
    const footer = document.querySelector('.footer');
    
    if (selectedFiles.size > 0) {{
        batchBar.classList.add('active');
        if (footer) footer.classList.add('hidden-by-batch');
        batchCount.textContent = `${{selectedFiles.size}} selected`;
    }} else {{
        batchBar.classList.remove('active');
        if (footer) footer.classList.remove('hidden-by-batch');
    }}
}}

function downloadSelected() {{
    if (selectedFiles.size === 0) return;
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '{DOWNLOAD_SELECTED}';
    
    const pathInput = document.createElement('input');
    pathInput.type = 'hidden';
    pathInput.name = 'p';
    pathInput.value = '{escape_html(current_path)}';
    form.appendChild(pathInput);
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = '_csrf';
    csrfInput.value = '{escape_html(csrf_token)}';
    form.appendChild(csrfInput);
    
    selectedFiles.forEach(f => {{
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'files';
        input.value = f;
        form.appendChild(input);
    }});
    
    document.body.appendChild(form);
    form.submit();
}}

function deleteSelected() {{
    if (selectedFiles.size === 0) return;
    
    if (!confirm(`Delete ${{selectedFiles.size}} items?`)) return;
    
    selectedFiles.forEach(path => {{
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '{DELETE}';
        
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'p';
        input.value = path;
        form.appendChild(input);
        
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = '_csrf';
        csrfInput.value = '{escape_html(csrf_token)}';
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    }});
}}

function toggleHidden(show) {{
    const url = new URL(window.location);
    url.searchParams.set('hidden', show ? '1' : '0');
    window.location.href = url.toString();
}}

function confirmDelete(name) {{
    return confirm(`Delete "${{name}}"?`);
}}

// File input change handler
const fileInput = document.getElementById('file-input');
if (fileInput) {{
    fileInput.addEventListener('change', function() {{
        if (this.files.length > 0) {{
            document.getElementById('upload-form').submit();
        }}
    }});
}}

// Drag and drop
const uploadZone = document.getElementById('upload-zone');
if (uploadZone) {{
    ['dragenter', 'dragover'].forEach(eventName => {{
        uploadZone.addEventListener(eventName, e => {{
            e.preventDefault();
            e.stopPropagation();
            uploadZone.classList.add('dragover');
        }});
    }});
    
    ['dragleave', 'drop'].forEach(eventName => {{
        uploadZone.addEventListener(eventName, e => {{
            e.preventDefault();
            e.stopPropagation();
            uploadZone.classList.remove('dragover');
        }});
    }});
    
    uploadZone.addEventListener('drop', e => {{
        const input = uploadZone.querySelector('input[type="file"]');
        if (input) {{
            input.files = e.dataTransfer.files;
            input.dispatchEvent(new Event('change'));
        }}
    }});
}}
</script>
"""
    return html





def _get_display_name(path: str) -> str:
    if not path:
        return "Files"
    return path.rstrip('/').split('/')[-1]


def _render_file_item(file_info: FileInfo, current_path: str, features: dict, csrf_token: str, search_query: str = "") -> str:
    icon = get_icon_for_file(file_info.name, file_info.is_dir)
    encoded_path = quote(file_info.path)
    name_class = "file-name is-dir" if file_info.is_dir else "file-name"
    display_name = escape_html(file_info.path if search_query else file_info.name)
    
    if file_info.is_dir:
        link = f'<a href="/?p={encoded_path}">{display_name}</a>'
    elif file_info.is_text and features.get("edit", True):
        link = f'<a href="/?p={encoded_path}&edit=1">{display_name}</a>'
    else:
        link = f'<a href="{RAW}?p={encoded_path}">{display_name}</a>'
    
    meta_parts = []
    if not file_info.is_dir:
        meta_parts.append(format_size(file_info.size))
    meta_parts.append(file_info.modified_str)
    meta_html = ' · '.join(meta_parts)
    
    icon_class = "file-icon folder" if file_info.is_dir else "file-icon"
    
    # Build download button
    download_html = ''
    if file_info.is_dir:
        download_html = f'<a href="{DOWNLOAD}?p={encoded_path}" class="file-action-btn" title="Download as ZIP">\U0001f4e5</a>'
    else:
        download_html = f'<a href="{RAW}?p={encoded_path}" class="file-action-btn" title="Download">\U0001f4e5</a>'
    
    return f'''
    <div class="file-group" style="margin-bottom: 2px;">
        <div class="file-item" data-path="{escape_html(file_info.path)}">
            <div class="file-checkbox" onclick="event.stopPropagation(); toggleFileSelect('{escape_html(file_info.path)}', this)"></div>
            <div class="{icon_class}">{icon}</div>
            <div class="file-info">
                <div class="{name_class}">{link}</div>
                <div class="file-meta">{meta_html}</div>
            </div>
            {download_html}
        </div>
    </div>'''


def _build_pagination(page: int, total_pages: int, current_path: str, search_query: str) -> str:
    if total_pages <= 1:
        return ""
    encoded_path = quote(current_path)
    encoded_query = quote(search_query) if search_query else ""
    buttons = []
    
    if page > 1:
        buttons.append(f'<a href="/?p={encoded_path}&page={page-1}&q={encoded_query}" class="btn btn-sm btn-ghost">\u2190 Previous</a>')
    
    start = max(1, page - 2)
    end = min(total_pages, page + 2)
    
    if start > 1:
        buttons.append(f'<a href="/?p={encoded_path}&page=1&q={encoded_query}" class="btn btn-sm btn-ghost">1</a>')
        if start > 2:
            buttons.append('<span style="color: var(--text-muted);">...</span>')
    
    for p in range(start, end + 1):
        if p == page:
            buttons.append(f'<span class="btn btn-sm" style="background: var(--accent-bg); color: var(--accent);">{p}</span>')
        else:
            buttons.append(f'<a href="/?p={encoded_path}&page={p}&q={encoded_query}" class="btn btn-sm btn-ghost">{p}</a>')
    
    if end < total_pages:
        if end < total_pages - 1:
            buttons.append('<span style="color: var(--text-muted);">...</span>')
        buttons.append(f'<a href="/?p={encoded_path}&page={total_pages}&q={encoded_query}" class="btn btn-sm btn-ghost">{total_pages}</a>')
    
    if page < total_pages:
        buttons.append(f'<a href="/?p={encoded_path}&page={page+1}&q={encoded_query}" class="btn btn-sm btn-ghost">Next \u2192</a>')
    
    return f'<div style="display: flex; justify-content: center; gap: 8px; margin: 24px 0; flex-wrap: wrap;">{"".join(buttons)}</div>'
