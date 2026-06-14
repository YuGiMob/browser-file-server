"""
File editor template.
"""

from urllib.parse import quote
from typing import Optional


def render_editor(
    file_path: str,
    content: str,
    flash_message: str = "",
    flash_type: str = "success",
    read_only: bool = False,
) -> str:
    """
    Render file editor HTML.

    Args:
        file_path: Path to the file
        content: File content
        flash_message: Flash message to display
        flash_type: Flash message type
        read_only: Whether the editor is read-only

    Returns:
        HTML string
    """
    encoded_path = quote(file_path)
    flash_html = ""
    if flash_message:
        flash_html = f'<div class="flash flash-{flash_type}">{flash_message}</div>'

    # Get file extension for syntax hint
    ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ""
    language_hint = _get_language_hint(ext)

    read_only_attr = "readonly" if read_only else ""
    read_only_class = "read-only" if read_only else ""

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
            <a href="/?p={encoded_path}" class="btn btn-sm btn-outline">👁️ View</a>
            <a href="/raw?p={encoded_path}" class="btn btn-sm btn-outline">⬇️ Download</a>
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌓</button>
        </div>
    </div>
</div>

<div class="container">
    {flash_html}
    
    <div class="editor-container">
        <form method="post" action="/save" id="editor-form">
            <input type="hidden" name="p" value="{file_path}">
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="color: var(--text-secondary); font-size: 12px;">
                        {language_hint}
                    </span>
                    <span id="line-count" style="color: var(--text-muted); font-size: 12px;"></span>
                    <span id="char-count" style="color: var(--text-muted); font-size: 12px;"></span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button type="button" class="btn btn-sm btn-outline" onclick="undoEdit()">↩️ Undo</button>
                    <button type="button" class="btn btn-sm btn-outline" onclick="redoEdit()">↪️ Redo</button>
                    <button type="button" class="btn btn-sm btn-outline" onclick="toggleWordWrap()">📝 Wrap</button>
                    {'<button type="submit" class="btn btn-success">💾 Save</button>' if not read_only else ''}
                </div>
            </div>
            
            <textarea 
                name="content" 
                id="editor"
                class="editor-textarea {read_only_class}"
                spellcheck="false"
                {read_only_attr}
                oninput="updateCounts()"
                onkeydown="handleTab(event)"
            >{_escape_html(content)}</textarea>
            
            <div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; gap: 16px; color: var(--text-muted); font-size: 12px;">
                    <span>💡 Press <kbd>Ctrl</kbd>+<kbd>S</kbd> to save</span>
                    <span>💡 Press <kbd>Tab</kbd> to indent</span>
                    <span>💡 Press <kbd>Shift</kbd>+<kbd>Tab</kbd> to unindent</span>
                </div>
                <div id="save-status" style="color: var(--text-muted); font-size: 12px;"></div>
            </div>
        </form>
    </div>
</div>

<script>
const editor = document.getElementById('editor');
let undoStack = [];
let redoStack = [];
let lastContent = editor.value;

// Update line and character counts
function updateCounts() {{
    const text = editor.value;
    const lines = text.split('\\n').length;
    const chars = text.length;
    document.getElementById('line-count').textContent = `Lines: ${{lines}}`;
    document.getElementById('char-count').textContent = `Characters: ${{chars}}`;
}}

// Handle tab key
function handleTab(e) {{
    if (e.key === 'Tab') {{
        e.preventDefault();
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        
        if (e.shiftKey) {{
            // Unindent
            const lineStart = editor.value.lastIndexOf('\\n', start - 1) + 1;
            const line = editor.value.substring(lineStart, end);
            if (line.startsWith('    ')) {{
                editor.value = editor.value.substring(0, lineStart) + line.substring(4) + editor.value.substring(end);
                editor.selectionStart = editor.selectionEnd = start - 4;
            }}
        }} else {{
            // Indent
            editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
            editor.selectionStart = editor.selectionEnd = start + 4;
        }}
        
        updateCounts();
    }}
}}

// Undo/Redo
function undoEdit() {{
    if (undoStack.length > 0) {{
        redoStack.push(editor.value);
        editor.value = undoStack.pop();
        updateCounts();
    }}
}}

function redoEdit() {{
    if (redoStack.length > 0) {{
        undoStack.push(editor.value);
        editor.value = redoStack.pop();
        updateCounts();
    }}
}}

// Track changes for undo
editor.addEventListener('input', function() {{
    if (editor.value !== lastContent) {{
        undoStack.push(lastContent);
        redoStack = [];
        lastContent = editor.value;
    }}
}});

// Word wrap toggle
let wordWrap = true;
function toggleWordWrap() {{
    wordWrap = !wordWrap;
    editor.style.whiteSpace = wordWrap ? 'pre-wrap' : 'pre';
    editor.style.overflowX = wordWrap ? 'hidden' : 'auto';
}}

// Auto-save indicator
let saveTimeout;
editor.addEventListener('input', function() {{
    clearTimeout(saveTimeout);
    const status = document.getElementById('save-status');
    status.textContent = 'Modified';
    status.style.color = 'var(--warning)';
    
    saveTimeout = setTimeout(() => {{
        status.textContent = '';
    }}, 2000);
}});

// Save with Ctrl+S
document.addEventListener('keydown', function(e) {{
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {{
        e.preventDefault();
        document.getElementById('editor-form').submit();
    }}
    
    // Ctrl+Z for undo
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {{
        e.preventDefault();
        undoEdit();
    }}
    
    // Ctrl+Y or Ctrl+Shift+Z for redo
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {{
        e.preventDefault();
        redoEdit();
    }}
}});

// Initialize counts
updateCounts();
</script>
"""

    return html


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


def _get_language_hint(ext: str) -> str:
    """Get language hint from file extension."""
    hints = {
        "py": "Python",
        "js": "JavaScript",
        "ts": "TypeScript",
        "jsx": "React JSX",
        "tsx": "React TSX",
        "html": "HTML",
        "htm": "HTML",
        "css": "CSS",
        "scss": "SCSS",
        "sass": "Sass",
        "less": "Less",
        "json": "JSON",
        "yaml": "YAML",
        "yml": "YAML",
        "xml": "XML",
        "toml": "TOML",
        "md": "Markdown",
        "markdown": "Markdown",
        "sh": "Shell",
        "bash": "Bash",
        "zsh": "Zsh",
        "fish": "Fish",
        "sql": "SQL",
        "go": "Go",
        "rs": "Rust",
        "java": "Java",
        "kt": "Kotlin",
        "swift": "Swift",
        "c": "C",
        "cpp": "C++",
        "h": "C Header",
        "hpp": "C++ Header",
        "cs": "C#",
        "rb": "Ruby",
        "php": "PHP",
        "pl": "Perl",
        "lua": "Lua",
        "r": "R",
        "vue": "Vue",
        "svelte": "Svelte",
    }

    return hints.get(ext, "Plain Text")
