"""
Base HTML template with theme support and mobile-first design.
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
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <meta name="description" content="Browser File Server">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#1e1e1e">
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
            --radius: 8px;
            --radius-lg: 12px;
            --transition: 0.2s ease;
            --safe-bottom: env(safe-area-inset-bottom, 0px);
            --safe-top: env(safe-area-inset-top, 0px);
        }}

        [data-theme="light"] {{
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #e9ecef;
            --bg-hover: #f1f3f5;
            --text-primary: #212529;
            --text-secondary: #6c757d;
            --text-muted: #adb5bd;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --success: #10b981;
            --success-hover: #059669;
            --danger: #ef4444;
            --danger-hover: #dc2626;
            --warning: #f59e0b;
            --info: #3b82f6;
            --border: #dee2e6;
            --shadow: rgba(0, 0, 0, 0.08);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }}

        html {{
            height: 100%;
            overflow-x: hidden;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 16px;
            line-height: 1.5;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100%;
            padding-bottom: calc(80px + var(--safe-bottom));
            -webkit-text-size-adjust: 100%;
        }}

        a {{
            color: var(--accent);
            text-decoration: none;
            transition: color var(--transition);
        }}

        a:hover, a:active {{
            color: var(--accent-hover);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 16px;
        }}

        /* Toolbar - Fixed at top */
        .toolbar {{
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 12px 0;
            position: sticky;
            top: 0;
            z-index: 100;
            padding-top: calc(12px + var(--safe-top));
        }}

        .toolbar-content {{
            display: flex;
            flex-direction: column;
            gap: 10px;
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
            font-size: 14px;
            color: var(--text-secondary);
            flex-wrap: wrap;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            flex: 1;
            min-width: 0;
        }}

        .breadcrumb::-webkit-scrollbar {{
            display: none;
        }}

        .breadcrumb a {{
            color: var(--accent);
            white-space: nowrap;
        }}

        .breadcrumb .separator {{
            color: var(--text-muted);
        }}

        .breadcrumb .current {{
            color: var(--text-primary);
            font-weight: 500;
            white-space: nowrap;
        }}

        /* Buttons - Touch friendly */
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 10px 16px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: var(--radius);
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: all var(--transition);
            white-space: nowrap;
            text-decoration: none;
            min-height: 44px;
            touch-action: manipulation;
            user-select: none;
            -webkit-user-select: none;
        }}

        .btn:hover, .btn:active {{
            background: var(--accent-hover);
            color: white;
            text-decoration: none;
        }}

        .btn:active {{
            transform: scale(0.98);
        }}

        .btn-sm {{
            padding: 8px 12px;
            font-size: 14px;
            min-height: 36px;
        }}

        .btn-success {{
            background: var(--success);
        }}

        .btn-success:hover, .btn-success:active {{
            background: var(--success-hover);
        }}

        .btn-danger {{
            background: var(--danger);
        }}

        .btn-danger:hover, .btn-danger:active {{
            background: var(--danger-hover);
        }}

        .btn-outline {{
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-primary);
        }}

        .btn-outline:hover, .btn-outline:active {{
            background: var(--bg-hover);
            border-color: var(--accent);
            color: var(--accent);
        }}

        /* Input - Mobile friendly */
        input[type="text"],
        input[type="password"],
        input[type="search"],
        textarea,
        select {{
            padding: 10px 14px;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            font-size: 16px;
            font-family: inherit;
            transition: all var(--transition);
            width: 100%;
            min-height: 44px;
        }}

        input[type="text"]:focus,
        input[type="password"]:focus,
        input[type="search"]:focus,
        textarea:focus,
        select:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(122, 162, 247, 0.2);
        }}

        input[type="file"] {{
            color: var(--text-primary);
        }}

        /* Checkbox - Larger for mobile */
        input[type="checkbox"] {{
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: var(--accent);
            flex-shrink: 0;
        }}

        /* File list */
        .file-list {{
            list-style: none;
            margin: 12px 0;
        }}

        .file-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            transition: background var(--transition);
            min-height: 60px;
        }}

        .file-item:hover, .file-item:active {{
            background: var(--bg-hover);
        }}

        .file-item:first-child {{
            border-top: 1px solid var(--border);
        }}

        .file-checkbox {{
            width: 22px;
            height: 22px;
            cursor: pointer;
            accent-color: var(--accent);
            flex-shrink: 0;
        }}

        .file-icon {{
            font-size: 24px;
            width: 32px;
            text-align: center;
            flex-shrink: 0;
        }}

        .file-info {{
            flex: 1;
            min-width: 0;
        }}

        .file-name {{
            font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 15px;
            word-break: break-all;
            line-height: 1.3;
        }}

        .file-name a {{
            color: var(--text-primary);
            display: block;
            padding: 2px 0;
        }}

        .file-name a:hover, .file-name a:active {{
            color: var(--accent);
        }}

        .file-name.is-dir a {{
            color: #c586c0;
        }}

        .file-meta {{
            display: flex;
            gap: 12px;
            color: var(--text-secondary);
            font-size: 13px;
            margin-top: 4px;
            flex-wrap: wrap;
        }}

        .file-actions {{
            display: flex;
            gap: 6px;
            flex-shrink: 0;
            flex-wrap: wrap;
            justify-content: flex-end;
        }}

        /* Flash messages */
        .flash {{
            padding: 14px 16px;
            border-radius: var(--radius);
            margin: 12px 0;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 15px;
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
            padding: 12px;
        }}

        .editor-textarea {{
            width: 100%;
            min-height: 60vh;
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.6;
            padding: 14px;
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
            border-radius: var(--radius-lg);
            text-align: center;
            transition: all var(--transition);
            margin: 12px 0;
            cursor: pointer;
        }}

        .upload-zone.dragover {{
            border-color: var(--accent);
            background: rgba(122, 162, 247, 0.1);
        }}

        .upload-zone-text {{
            color: var(--text-secondary);
            margin-bottom: 12px;
            font-size: 15px;
        }}

        /* Toast notifications */
        .toast-container {{
            position: fixed;
            bottom: calc(20px + var(--safe-bottom));
            left: 16px;
            right: 16px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 8px;
            pointer-events: none;
        }}

        .toast {{
            padding: 14px 16px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: 0 4px 12px var(--shadow);
            animation: slideUp 0.3s ease;
            pointer-events: auto;
            font-size: 15px;
        }}

        @keyframes slideUp {{
            from {{
                transform: translateY(100%);
                opacity: 0;
            }}
            to {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}

        /* Preview */
        .preview-container {{
            padding: 12px;
        }}

        .preview-image {{
            max-width: 100%;
            max-height: 70vh;
            border-radius: var(--radius);
            display: block;
            margin: 0 auto;
        }}

        .preview-video,
        .preview-audio {{
            width: 100%;
            max-width: 100%;
        }}

        .preview-code {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 14px;
            overflow-x: auto;
            font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            -webkit-overflow-scrolling: touch;
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
            align-items: flex-end;
            justify-content: center;
            z-index: 1000;
            padding: 16px;
        }}

        .modal {{
            background: var(--bg-secondary);
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
            padding: 24px;
            width: 100%;
            max-width: 500px;
            box-shadow: 0 -4px 20px var(--shadow);
            max-height: 80vh;
            overflow-y: auto;
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

        /* Footer - Fixed at bottom for mobile */
        .footer {{
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
            padding: 12px 0;
            padding-bottom: calc(12px + var(--safe-bottom));
            color: var(--text-secondary);
            font-size: 12px;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 50;
        }}

        .footer-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }}

        /* Responsive - Mobile First */
        @media (max-width: 768px) {{
            body {{
                font-size: 16px;
            }}

            .toolbar-row {{
                flex-direction: column;
                align-items: stretch;
            }}

            .toolbar-row .btn,
            .toolbar-row .btn-sm {{
                width: 100%;
                justify-content: center;
            }}

            .search-form {{
                width: 100%;
                max-width: none;
            }}

            .search-form .btn {{
                flex-shrink: 0;
            }}

            .file-item {{
                flex-wrap: wrap;
                padding: 12px;
                gap: 8px;
            }}

            .file-checkbox {{
                order: -1;
            }}

            .file-icon {{
                font-size: 28px;
                width: 36px;
            }}

            .file-info {{
                flex: 1;
                min-width: calc(100% - 80px);
            }}

            .file-actions {{
                width: 100%;
                justify-content: flex-start;
                padding-left: 48px;
                gap: 8px;
            }}

            .file-actions .btn {{
                flex: 1;
                min-width: 0;
                justify-content: center;
                font-size: 13px;
                padding: 8px 10px;
            }}

            .filter-bar {{
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
                flex-wrap: nowrap;
                padding-bottom: 4px;
            }}

            .filter-bar::-webkit-scrollbar {{
                display: none;
            }}

            .filter-btn {{
                white-space: nowrap;
                flex-shrink: 0;
            }}

            .modal {{
                border-radius: var(--radius-lg);
                margin: auto;
            }}

            .modal-overlay {{
                align-items: center;
            }}
        }}

        /* Tablet */
        @media (min-width: 769px) and (max-width: 1024px) {{
            .file-actions .btn {{
                font-size: 13px;
                padding: 6px 10px;
            }}
        }}

        /* Theme toggle */
        .theme-toggle {{
            background: none;
            border: none;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 24px;
            padding: 8px;
            transition: transform var(--transition);
            min-width: 44px;
            min-height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .theme-toggle:hover, .theme-toggle:active {{
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
            margin: 12px 0;
        }}

        .filter-btn {{
            padding: 8px 14px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            color: var(--text-primary);
            cursor: pointer;
            font-size: 14px;
            transition: all var(--transition);
            min-height: 40px;
        }}

        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }}

        /* Batch actions */
        .batch-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .selected-count {{
            color: var(--text-secondary);
            font-size: 13px;
        }}

        /* Hidden */
        .hidden {{
            display: none !important;
        }}

        /* Keyboard shortcuts hint */
        .shortcuts-hint {{
            color: var(--text-muted);
            font-size: 11px;
            display: none;
        }}

        @media (min-width: 769px) {{
            .shortcuts-hint {{
                display: inline;
            }}
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

        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 48px 16px;
            color: var(--text-secondary);
        }}

        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}

        .empty-state-text {{
            font-size: 16px;
        }}

        /* Loading state */
        .loading {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 32px;
            color: var(--text-secondary);
        }}

        .loading-spinner {{
            width: 24px;
            height: 24px;
            border: 3px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 12px;
        }}

        @keyframes spin {{
            to {{
                transform: rotate(360deg);
            }}
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
            <span>File Server v{version}</span>
            <span class="shortcuts-hint">
                <kbd>Ctrl</kbd>+<kbd>S</kbd> Save | 
                <kbd>/</kbd> Search
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
    
    // Update meta theme color
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) {{
        metaTheme.content = next === 'light' ? '#f8f9fa' : '#1e1e1e';
    }}
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
        toast.style.transform = 'translateY(100%)';
        toast.style.transition = 'all 0.3s ease';
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
    
    // Click to upload on mobile
    uploadZone.addEventListener('click', e => {{
        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT') {{
            const input = uploadZone.querySelector('input[type="file"]');
            if (input) {{
                input.click();
            }}
        }}
    }});
}}

// Prevent double tap zoom on iOS
document.addEventListener('touchend', e => {{
    const now = Date.now();
    if (now - (window.lastTouchEnd || 0) < 300) {{
        e.preventDefault();
    }}
    window.lastTouchEnd = now;
}}, false);
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
