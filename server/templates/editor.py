"""
File editor template with professional mobile-app design.
"""

from urllib.parse import quote
from ..utils.format import escape_html
from ..utils.path import get_parent_path, build_path_breadcrumb
from .. import RAW, SAVE
from .base import _render_header
def render_editor(
    file_path: str,
    content: str,
    flash_message: str = "",
    flash_type: str = "success",
    read_only: bool = False,
    csrf_token: str = "",
) -> str:
    """
    Render file editor HTML.

    Args:
        file_path: Path to the file
        content: File content
        flash_message: Flash message to display
        flash_type: Flash message type
        read_only: Whether the editor is read-only
        csrf_token: CSRF token for form submission

    Returns:
        HTML string
    """
    encoded_path = quote(file_path)
    safe_file_path = escape_html(file_path)
    safe_file_name = escape_html(file_path.split('/')[-1])
    
    flash_html = ""
    if flash_message:
        flash_html = f'<div class="flash flash-{flash_type}">{flash_message}</div>'

    # Get file extension for syntax hint
    ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ""
    language_hint = _get_language_hint(ext)

    read_only_attr = "readonly" if read_only else ""

    actions = f'''
        <a href="/?p={encoded_path}" class="btn-icon" title="View">👁️</a>
        <a href="/raw?p={encoded_path}" class="btn-icon" title="Download">⬇️</a>
    '''
    breadcrumb = f'<a href="/">/</a>{build_path_breadcrumb(file_path)}'
    header_html = _render_header(
        back_url=f"/?p={quote(get_parent_path(file_path))}",
        title=safe_file_name,
        actions_html=actions,
        breadcrumb_html=breadcrumb,
    )
    html = f"""
    {header_html}
    <div class="container">
    {flash_html}

    <div class="editor-container">
        <form method="post" action="{SAVE}" id="editor-form">
            <input type="hidden" name="p" value="{safe_file_path}">
            <input type="hidden" name="_csrf" value="{escape_html(csrf_token)}">

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="color: var(--text-secondary); font-size: 13px;">
                        {escape_html(language_hint)}
                    </span>
                    <span id="line-count" style="color: var(--text-muted); font-size: 13px;"></span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button type="button" class="btn btn-sm btn-ghost" onclick="undoEdit()">\U0001f649</button>
                    <button type="button" class="btn btn-sm btn-ghost" onclick="redoEdit()">\U0001f64a</button>
                    {'<button type="submit" class="btn btn-sm">Save</button>' if not read_only else ''}
                </div>
            </div>

            <div id="editor-container" style="border: none; border-radius: var(--radius); overflow: hidden; display: none;"></div>
            <textarea name="content" id="editor-textarea" style="width: 100%; min-height: 60vh; background: var(--bg-secondary); color: var(--text-primary); border: none; border-radius: var(--radius); font-family: 'SF Mono', 'Menlo', 'Consolas', monospace; font-size: 15px; line-height: 1.6; padding: 16px; resize: vertical; tab-size: 4; -webkit-appearance: none;">{escape_html(content)}</textarea>

            <div style="margin-top: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="color: var(--text-muted); font-size: 13px;">
                    <span id="char-count"></span>
                </div>
                <div id="save-status" style="color: var(--text-muted); font-size: 13px;"></div>
            </div>
        </form>
    </div>
    </div>

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/theme/material-darker.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/python/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/javascript/javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/xml/xml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/htmlmixed/htmlmixed.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/css/css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/markdown/markdown.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/sql/sql.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/yaml/yaml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/clike/clike.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/shell/shell.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/ruby/ruby.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/php/php.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/go/go.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/rust/rust.min.js"></script>
    <script>
    const MODE_MAP = {{
        'py': 'python', 'js': 'javascript', 'ts': 'text/typescript',
        'jsx': 'text/jsx', 'tsx': 'text/jsx',
        'html': 'htmlmixed', 'htm': 'htmlmixed',
        'css': 'css', 'scss': 'text/x-scss',
        'json': 'application/json', 'xml': 'xml',
        'yaml': 'yaml', 'yml': 'yaml',
        'toml': 'toml', 'md': 'markdown',
        'sh': 'shell', 'bash': 'shell',
        'sql': 'sql', 'go': 'go', 'rs': 'rust',
        'java': 'text/x-java', 'c': 'text/x-csrc',
        'cpp': 'text/x-c++src', 'h': 'text/x-csrc',
        'cs': 'text/x-csharp', 'rb': 'ruby',
        'php': 'php',
    }};
    const ext = '{ext}';
    const mode = MODE_MAP[ext] || null;

    const textarea = document.getElementById('editor-textarea');
    let editor = null;

    if (typeof CodeMirror !== 'undefined') {{
        try {{
            editor = CodeMirror(document.getElementById('editor-container'), {{
                value: textarea.value,
                mode: mode,
                theme: 'material-darker',
                lineNumbers: true,
                indentUnit: 4,
                tabSize: 4,
                indentWithTabs: false,
                lineWrapping: false,
                viewportMargin: Infinity,
                readOnly: {'true' if read_only else 'false'},
                extraKeys: {{
                    'Tab': function(cm) {{ cm.replaceSelection('    ', 'end'); }},
                    'Shift-Tab': function(cm) {{ cm.execCommand('indentLess'); }},
                }},
            }});
            document.getElementById('editor-container').style.display = '';
            textarea.style.display = 'none';
        }} catch (e) {{
            textarea.style.display = '';
        }}
    }} else {{
        textarea.style.display = '';
    }}

    document.getElementById('editor-form').addEventListener('submit', function() {{
        if (editor) {{
            textarea.value = editor.getValue();
        }}
    }});

    function updateCounts() {{
        const text = editor ? editor.getValue() : textarea.value;
        const lines = text.split('\n').length;
        const chars = text.length;
        document.getElementById('line-count').textContent = lines + ' lines';
        document.getElementById('char-count').textContent = chars + ' chars';
    }}

    let undoStack = [];
    let redoStack = [];
    let lastContent = editor ? editor.getValue() : textarea.value;

    function onContentChange() {{
        const val = editor ? editor.getValue() : textarea.value;
        if (val !== lastContent) {{
            if (undoStack.length >= 100) undoStack.shift();
            undoStack.push(lastContent);
            redoStack = [];
            lastContent = val;
        }}
        updateCounts();
        clearTimeout(window._saveTimeout);
        const status = document.getElementById('save-status');
        status.textContent = 'Modified';
        status.style.color = 'var(--warning)';
        window._saveTimeout = setTimeout(function() {{
            status.textContent = '';
        }}, 2000);
    }}

    if (editor) {{
        editor.on('change', onContentChange);
    }} else {{
        textarea.addEventListener('input', onContentChange);
    }}

    function undoEdit() {{
        if (undoStack.length > 0) {{
            redoStack.push(editor ? editor.getValue() : textarea.value);
            const val = undoStack.pop();
            if (editor) editor.setValue(val);
            else textarea.value = val;
            updateCounts();
        }}
    }}

    function redoEdit() {{
        if (redoStack.length > 0) {{
            undoStack.push(editor ? editor.getValue() : textarea.value);
            const val = redoStack.pop();
            if (editor) editor.setValue(val);
            else textarea.value = val;
            updateCounts();
        }}
    }}

    document.addEventListener('keydown', function(e) {{
        if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {{
            e.preventDefault();
            undoEdit();
        }}
        if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {{
            e.preventDefault();
            redoEdit();
        }}
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {{
            e.preventDefault();
            document.getElementById('editor-form').requestSubmit();
        }}
    }});

    updateCounts();
    </script>
"""
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
        "json": "JSON",
        "yaml": "YAML",
        "yml": "YAML",
        "xml": "XML",
        "toml": "TOML",
        "md": "Markdown",
        "sh": "Shell",
        "bash": "Bash",
        "sql": "SQL",
        "go": "Go",
        "rs": "Rust",
        "java": "Java",
        "c": "C",
        "cpp": "C++",
        "h": "C Header",
        "cs": "C#",
        "rb": "Ruby",
        "php": "PHP",
    }
    return hints.get(ext, "Text")
