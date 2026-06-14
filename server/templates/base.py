"""
Base HTML template with theme support.
"""

from typing import Dict, Optional
from urllib.parse import quote


def get_head(title: str, theme: str = "dark") -> str:
    """
    Get HTML head section.

    Args:
        title: Page title
        theme: Theme (dark, light, auto)

    Returns:
        HTML head string
    """
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="{theme}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Browser File Server">
    <title>{title} - File Server</title>
    <style>
        :root {{
            --bg-primary: #1e1e1e;
            --bg-secondary: #252526;
            --bg-tertiary: #2d2d2d;
            --bg-hover: #2a2d2e;
            --text-primary: #d4d4d4;
            --text-secondary: #888;
            --text-muted: #666;
            --accent: #7aa2f7;
            --accent-hover: #89b4fa;
            --success: #16825d;
            --success-hover: #1a9c6d;
            --danger: #a1260d;
            --danger-hover: #c4350d;
            --warning: #d19a66;
            --info: #61afef;
            --border: #3c3c3c;
            --shadow: rgba(0, 0, 0, 0.3);
            --radius: 6px;
            --transition: 0.2s ease;
        }}

        [data-theme="light"] {{
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --bg-tertiary: #e5e5e5;
            --bg-hover: #eeeeee;
            --text-primary: #333333;
            --text-secondary: #666666;
            --text-muted: #999999;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --success: #10b981;
            --success-hover: #059669;
            --danger: #ef4444;
            --danger-hover: #dc2626;
            --warning: #f59e0b;
            --info: #3b82f6;
            --border: #e5e7eb;
            --shadow: rgba(0, 0, 0, 0.1);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }}

        a {{
            color: var(--accent);
            text-decoration: none;
            transition: color var(--transition);
        }}

        a:hover {{
            color: var(--accent-hover);
            text-decoration: underline;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 16px;
        }}

        /* Header */
        .header {{
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 12px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .header-content {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .logo-icon {{
            font-size: 24px;
        }}

        /* Toolbar */
        .toolbar {{
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 12px 0;
        }}

        .toolbar-content {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .toolbar-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}

        /* Breadcrumb */
        .breadcrumb {{
            display: flex;
            align-items: center;
            gap: 4px;
            font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            color: var(--text-secondary);
            flex-wrap: wrap;
        }}

        .breadcrumb a {{
            color: var(--accent);
        }}

        .breadcrumb .separator {{
            color: var(--text-muted);
        }}

        .breadcrumb .current {{
            color: var(--text-primary);
            font-weight: 500;
        }}

        /* Buttons */
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 8px 16px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: var(--radius);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all var(--transition);
            white-space: nowrap;
            text-decoration: none;
        }}

        .btn:hover {{
            background: var(--accent-hover);
            color: white;
            text-decoration: none;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px var(--shadow);
        }}

        .btn:active {{
            transform: translateY(0);
        }}

        .btn-sm {{
            padding: 4px 10px;
            font-size: 12px;
        }}

        .btn-success {{
            background: var(--success);
        }}

        .btn-success:hover {{
            background: var(--success-hover);
        }}

        .btn-danger {{
            background: var(--danger);
        }}

        .btn-danger:hover {{
            background: var(--danger-hover);
        }}

        .btn-outline {{
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-primary);
        }}

        .btn-outline:hover {{
            background: var(--bg-hover);
            border-color: var(--accent);
            color: var(--accent);
        }}

        .btn-icon {{
            padding: 8px;
            min-width: 36px;
        }}

        /* Input */
        input[type="text"],
        input[type="password"],
        input[type="search"],
        textarea {{
            padding: 8px 12px;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            font-size: 14px;
            transition: all var(--transition);
        }}

        input[type="text"]:focus,
        input[type="password"]:focus,
        input[type="search"]:focus,
        textarea:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba(122, 162, 247, 0.2);
        }}

        input[type="file"] {{
            color: var(--text-primary);
        }}

        /* File list */
        .file-list {{
            list-style: none;
            margin: 16px 0;
        }}

        .file-checkbox {{
            width: 16px;
            height: 16px;
            cursor: pointer;
            accent-color: var(--accent);
            flex-shrink: 0;
        }}

        .file-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            transition: background var(--transition);
        }}

        .file-item:hover {{
            background: var(--bg-hover);
        }}

        .file-item:first-child {{
            border-top: 1px solid var(--border);
        }}

        .file-icon {{
            font-size: 20px;
            width: 24px;
            text-align: center;
            flex-shrink: 0;
        }}

        .file-info {{
            flex: 1;
            min-width: 0;
        }}

        .file-name {{
            font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 14px;
            word-break: break-all;
        }}

        .file-name a {{
            color: var(--text-primary);
        }}

        .file-name a:hover {{
            color: var(--accent);
        }}

        .file-name.is-dir a {{
            color: #c586c0;
        }}

        .file-meta {{
            display: flex;
            gap: 16px;
            color: var(--text-secondary);
            font-size: 12px;
            margin-top: 4px;
        }}

        .file-actions {{
            display: flex;
            gap: 6px;
            flex-shrink: 0;
        }}

        /* Flash messages */
        .flash {{
            padding: 12px 16px;
            border-radius: var(--radius);
            margin: 16px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .flash-success {{
            background: var(--success);
            color: white;
        }}

        .flash-error {{
            background: var(--danger);
            color: white;
        }}

        .flash-warning {{
            background: var(--warning);
            color: white;
        }}

        .flash-info {{
            background: var(--info);
            color: white;
        }}

        /* Editor */
        .editor-container {{
            padding: 16px;
        }}

        .editor-textarea {{
            width: 100%;
            min-height: 70vh;
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.6;
            padding: 16px;
            resize: vertical;
            tab-size: 4;
        }}

        .editor-textarea:focus {{
            outline: none;
            border-color: var(--accent);
        }}

        /* Upload zone */
        .upload-zone {{
            padding: 24px;
            background: var(--bg-secondary);
            border: 2px dashed var(--border);
            border-radius: var(--radius);
            text-align: center;
            transition: all var(--transition);
            margin: 16px 0;
        }}

        .upload-zone.dragover {{
            border-color: var(--accent);
            background: rgba(122, 162, 247, 0.1);
        }}

        .upload-zone-text {{
            color: var(--text-secondary);
            margin-bottom: 12px;
        }}

        /* Progress bar */
        .progress {{
            height: 4px;
            background: var(--bg-tertiary);
            border-radius: 2px;
            overflow: hidden;
            margin: 8px 0;
        }}

        .progress-bar {{
            height: 100%;
            background: var(--accent);
            transition: width 0.3s ease;
        }}

        /* Toast notifications */
        .toast-container {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .toast {{
            padding: 12px 16px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: 0 4px 12px var(--shadow);
            animation: slideIn 0.3s ease;
        }}

        @keyframes slideIn {{
            from {{
                transform: translateX(100%);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}

        /* Preview */
        .preview-container {{
            padding: 16px;
        }}

        .preview-image {{
            max-width: 100%;
            max-height: 80vh;
            border-radius: var(--radius);
        }}

        .preview-video,
        .preview-audio {{
            width: 100%;
            max-width: 800px;
        }}

        .preview-code {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px;
            overflow-x: auto;
            font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        /* Modal */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }}

        .modal {{
            background: var(--bg-secondary);
            border-radius: var(--radius);
            padding: 24px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 8px 32px var(--shadow);
        }}

        .modal-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
        }}

        .modal-actions {{
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            margin-top: 24px;
        }}

        /* Footer */
        .footer {{
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
            padding: 16px 0;
            margin-top: 32px;
            color: var(--text-secondary);
            font-size: 12px;
        }}

        .footer-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header-content {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .toolbar-row {{
                flex-direction: column;
                align-items: stretch;
            }}

            .file-item {{
                flex-wrap: wrap;
            }}

            .file-actions {{
                width: 100%;
                justify-content: flex-end;
            }}
        }}

        /* Theme toggle */
        .theme-toggle {{
            background: none;
            border: none;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 20px;
            padding: 4px;
            transition: transform var(--transition);
        }}

        .theme-toggle:hover {{
            transform: scale(1.1);
        }}

        /* Search */
        .search-form {{
            display: flex;
            gap: 8px;
            flex: 1;
            max-width: 400px;
        }}

        .search-input {{
            flex: 1;
        }}

        /* Filter */
        .filter-bar {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin: 16px 0;
        }}

        .filter-btn {{
            padding: 4px 12px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            color: var(--text-primary);
            cursor: pointer;
            font-size: 12px;
            transition: all var(--transition);
        }}

        .filter-btn:hover,
        .filter-btn.active {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }}

        /* Hidden */
        .hidden {{
            display: none !important;
        }}

        /* Keyboard shortcuts hint */
        .shortcuts-hint {{
            color: var(--text-muted);
            font-size: 11px;
        }}

        .kbd {{
            display: inline-block;
            padding: 2px 6px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 3px;
            font-family: monospace;
            font-size: 11px;
        }}
    </style>
</head>"""


def get_footer(version: str = "2.0.0") -> str:
    """
    Get HTML footer.

    Args:
        version: Server version

    Returns:
        HTML footer string
    """
    return f"""
<footer class="footer">
    <div class="container">
        <div class="footer-content">
            <span>Browser File Server v{version}</span>
            <span class="shortcuts-hint">
                <kbd>Ctrl</kbd>+<kbd>S</kbd> Save | 
                <kbd>/</kbd> Search | 
                <kbd>?</kbd> Help
            </span>
        </div>
    </div>
</footer>

<div class="toast-container" id="toast-container"></div>

<script>
// Theme management
const theme = localStorage.getItem('theme') || 'auto';
document.documentElement.setAttribute('data-theme', theme);

function toggleTheme() {{
    const current = document.documentElement.getAttribute('data-theme');
    let next;
    if (current === 'dark') next = 'light';
    else if (current === 'light') next = 'auto';
    else next = 'dark';
    
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}}

// Toast notifications
function showToast(message, type = 'info', duration = 3000) {{
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${{type}}`;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {{
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }}, duration);
}}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {{
    // Ctrl+S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {{
        const form = document.querySelector('form[method="post"]');
        if (form) {{
            e.preventDefault();
            form.submit();
        }}
    }}
    
    // / to focus search
    if (e.key === '/' && !e.ctrlKey && !e.metaKey) {{
        const searchInput = document.querySelector('input[type="search"]');
        if (searchInput && document.activeElement !== searchInput) {{
            e.preventDefault();
            searchInput.focus();
        }}
    }}
    
    // Escape to blur
    if (e.key === 'Escape') {{
        document.activeElement.blur();
    }}
}});

// Drag and drop upload
const uploadZone = document.querySelector('.upload-zone');
if (uploadZone) {{
    ['dragenter', 'dragover'].forEach(eventName => {{
        uploadZone.addEventListener(eventName, e => {{
            e.preventDefault();
            uploadZone.classList.add('dragover');
        }});
    }});
    
    ['dragleave', 'drop'].forEach(eventName => {{
        uploadZone.addEventListener(eventName, e => {{
            e.preventDefault();
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
</body>
</html>"""


def get_base_html(title: str, content: str, theme: str = "dark", version: str = "2.0.0") -> str:
    """
    Get complete HTML page.

    Args:
        title: Page title
        content: Page content
        theme: Theme (dark, light, auto)
        version: Server version

    Returns:
        Complete HTML string
    """
    return get_head(title, theme) + content + get_footer(version)
