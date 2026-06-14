"""
Base HTML template with professional mobile-app design.
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
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
    <meta name="description" content="Browser File Server">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#000000">
    <title>{title}</title>
    <style>
        :root {{
            --bg-primary: #000000;
            --bg-secondary: #1c1c1e;
            --bg-tertiary: #2c2c2e;
            --bg-card: #1c1c1e;
            --bg-hover: rgba(255, 255, 255, 0.05);
            --bg-active: rgba(255, 255, 255, 0.1);
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.6);
            --text-muted: rgba(255, 255, 255, 0.3);
            --accent: #0a84ff;
            --accent-hover: #409cff;
            --accent-bg: rgba(10, 132, 255, 0.15);
            --success: #30d158;
            --success-bg: rgba(48, 209, 88, 0.15);
            --danger: #ff453a;
            --danger-bg: rgba(255, 69, 58, 0.15);
            --warning: #ff9f0a;
            --warning-bg: rgba(255, 159, 10, 0.15);
            --border: rgba(255, 255, 255, 0.08);
            --shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            --radius: 12px;
            --radius-sm: 8px;
            --radius-lg: 16px;
            --transition: 0.2s ease;
            --safe-bottom: env(safe-area-inset-bottom, 0px);
            --safe-top: env(safe-area-inset-top, 0px);
            --safe-left: env(safe-area-inset-left, 0px);
            --safe-right: env(safe-area-inset-right, 0px);
        }}

        [data-theme="light"] {{
            --bg-primary: #f2f2f7;
            --bg-secondary: #ffffff;
            --bg-tertiary: #e5e5ea;
            --bg-card: #ffffff;
            --bg-hover: rgba(0, 0, 0, 0.03);
            --bg-active: rgba(0, 0, 0, 0.06);
            --text-primary: #000000;
            --text-secondary: rgba(0, 0, 0, 0.55);
            --text-muted: rgba(0, 0, 0, 0.3);
            --accent: #007aff;
            --accent-hover: #0056b3;
            --accent-bg: rgba(0, 122, 255, 0.1);
            --success: #34c759;
            --success-bg: rgba(52, 199, 89, 0.1);
            --danger: #ff3b30;
            --danger-bg: rgba(255, 59, 48, 0.1);
            --warning: #ff9500;
            --warning-bg: rgba(255, 149, 0, 0.1);
            --border: rgba(0, 0, 0, 0.08);
            --shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
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
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;
            font-size: 17px;
            line-height: 1.47;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100%;
            padding-bottom: calc(80px + var(--safe-bottom));
            -webkit-text-size-adjust: 100%;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        a {{
            color: var(--accent);
            text-decoration: none;
            transition: opacity var(--transition);
        }}

        a:hover, a:active {{
            opacity: 0.7;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 16px;
        }}

        /* Header - iOS style */
        .header {{
            background: var(--bg-secondary);
            border-bottom: 0.5px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
            padding-top: var(--safe-top);
        }}

        .header-content {{
            padding: 12px 16px;
        }}

        .header-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }}

        .header-title {{
            font-size: 17px;
            font-weight: 600;
            letter-spacing: -0.4px;
        }}

        .header-actions {{
            display: flex;
            gap: 8px;
        }}

        .breadcrumb {{
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 15px;
            color: var(--text-secondary);
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            padding: 4px 0;
        }}

        .breadcrumb::-webkit-scrollbar {{
            display: none;
        }}

        .breadcrumb a {{
            color: var(--accent);
            white-space: nowrap;
            padding: 4px 0;
        }}

        .breadcrumb .separator {{
            color: var(--text-muted);
        }}

        .breadcrumb .current {{
            color: var(--text-primary);
            font-weight: 500;
            white-space: nowrap;
        }}

        /* Search Bar - iOS style */
        .search-bar {{
            padding: 0 16px 12px;
        }}

        .search-input-wrapper {{
            position: relative;
            display: flex;
            align-items: center;
        }}

        .search-icon {{
            position: absolute;
            left: 12px;
            color: var(--text-muted);
            font-size: 15px;
            pointer-events: none;
        }}

        .search-input {{
            width: 100%;
            padding: 10px 12px 10px 36px;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: none;
            border-radius: 10px;
            font-size: 17px;
            font-family: inherit;
            -webkit-appearance: none;
            appearance: none;
        }}

        .search-input::placeholder {{
            color: var(--text-muted);
        }}

        .search-input:focus {{
            outline: none;
            background: var(--bg-tertiary);
        }}

        /* Buttons - iOS style */
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 10px 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 17px;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            transition: all var(--transition);
            white-space: nowrap;
            text-decoration: none;
            min-height: 44px;
            touch-action: manipulation;
            user-select: none;
            -webkit-user-select: none;
            letter-spacing: -0.4px;
        }}

        .btn:hover, .btn:active {{
            opacity: 0.85;
            color: white;
            text-decoration: none;
        }}

        .btn:active {{
            transform: scale(0.97);
        }}

        .btn-sm {{
            padding: 8px 16px;
            font-size: 15px;
            min-height: 36px;
            border-radius: 8px;
        }}

        .btn-icon {{
            width: 44px;
            height: 44px;
            padding: 0;
            border-radius: 50%;
            background: transparent;
            color: var(--text-primary);
        }}

        .btn-icon:hover, .btn-icon:active {{
            background: var(--bg-hover);
            opacity: 1;
        }}

        .btn-ghost {{
            background: transparent;
            color: var(--accent);
        }}

        .btn-ghost:hover, .btn-ghost:active {{
            background: var(--accent-bg);
            opacity: 1;
        }}

        .btn-danger {{
            background: transparent;
            color: var(--danger);
        }}

        .btn-danger:hover, .btn-danger:active {{
            background: var(--danger-bg);
            opacity: 1;
        }}

        /* Toolbar Actions */
        .toolbar {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }}

        .toolbar::-webkit-scrollbar {{
            display: none;
        }}

        .toolbar-spacer {{
            flex: 1;
        }}

        /* Segmented Control - iOS style */
        .segmented-control {{
            display: flex;
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 2px;
            gap: 2px;
        }}

        .segmented-btn {{
            padding: 6px 12px;
            background: transparent;
            border: none;
            border-radius: 6px;
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 500;
            font-family: inherit;
            cursor: pointer;
            transition: all var(--transition);
            white-space: nowrap;
        }}

        .segmented-btn.active {{
            background: var(--bg-secondary);
            color: var(--text-primary);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        /* File List - iOS style */
        .file-list {{
            list-style: none;
        }}

        .file-section {{
            margin: 8px 0;
        }}

        .file-section-header {{
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .file-group {{
            background: var(--bg-card);
            border-radius: var(--radius);
            margin: 0 16px;
            overflow: hidden;
        }}

        .file-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: var(--bg-card);
            transition: background var(--transition);
            cursor: pointer;
            position: relative;
        }}

        .file-item:not(:last-child)::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 60px;
            right: 0;
            height: 0.5px;
            background: var(--border);
        }}

        .file-item:active {{
            background: var(--bg-active);
        }}

        .file-item.selected {{
            background: var(--accent-bg);
        }}

        .file-checkbox {{
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 2px solid var(--text-muted);
            cursor: pointer;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition);
        }}

        .file-checkbox.checked {{
            background: var(--accent);
            border-color: var(--accent);
        }}

        .file-checkbox.checked::after {{
            content: '✓';
            color: white;
            font-size: 14px;
            font-weight: 600;
        }}

        .file-icon {{
            width: 44px;
            height: 44px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            flex-shrink: 0;
            background: var(--bg-tertiary);
        }}

        .file-icon.folder {{
            background: var(--accent-bg);
        }}

        .file-info {{
            flex: 1;
            min-width: 0;
        }}

        .file-name {{
            font-size: 17px;
            font-weight: 400;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            letter-spacing: -0.4px;
        }}

        .file-name a {{
            color: inherit;
            display: block;
        }}

        .file-name.is-dir a {{
            color: var(--accent);
        }}

        .file-meta {{
            display: flex;
            gap: 8px;
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 2px;
        }}

        .file-action-btn {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition);
            flex-shrink: 0;
        }}

        .file-action-btn:active {{
            background: var(--bg-active);
        }}

        /* Flash Messages */
        .flash {{
            padding: 12px 16px;
            border-radius: var(--radius);
            margin: 12px 16px;
            font-size: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .flash-success {{
            background: var(--success-bg);
            color: var(--success);
        }}

        .flash-error {{
            background: var(--danger-bg);
            color: var(--danger);
        }}

        .flash-warning {{
            background: var(--warning-bg);
            color: var(--warning);
        }}

        /* Editor */
        .editor-container {{
            padding: 16px;
        }}

        .editor-textarea {{
            width: 100%;
            min-height: 60vh;
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: none;
            border-radius: var(--radius);
            font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
            font-size: 15px;
            line-height: 1.6;
            padding: 16px;
            resize: vertical;
            tab-size: 4;
            -webkit-appearance: none;
        }}

        .editor-textarea:focus {{
            outline: none;
        }}

        /* Upload Zone */
        .upload-zone {{
            padding: 32px 16px;
            margin: 12px 16px;
            background: var(--bg-card);
            border: 2px dashed var(--border);
            border-radius: var(--radius-lg);
            text-align: center;
            transition: all var(--transition);
            cursor: pointer;
        }}

        .upload-zone.dragover {{
            border-color: var(--accent);
            background: var(--accent-bg);
        }}

        .upload-zone-icon {{
            font-size: 48px;
            margin-bottom: 12px;
        }}

        .upload-zone-text {{
            color: var(--text-secondary);
            font-size: 15px;
        }}

        .upload-zone-text strong {{
            color: var(--text-primary);
        }}

        /* Bottom Sheet - iOS style */
        .bottom-sheet {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--bg-secondary);
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
            padding: 16px;
            padding-bottom: calc(16px + var(--safe-bottom));
            box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
            z-index: 200;
            transform: translateY(100%);
            transition: transform 0.3s ease;
        }}

        .bottom-sheet.active {{
            transform: translateY(0);
        }}

        .bottom-sheet-handle {{
            width: 36px;
            height: 4px;
            background: var(--text-muted);
            border-radius: 2px;
            margin: 0 auto 16px;
        }}

        .bottom-sheet-title {{
            font-size: 17px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 16px;
        }}

        .bottom-sheet-actions {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .bottom-sheet-btn {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            background: var(--bg-card);
            border: none;
            border-radius: var(--radius);
            color: var(--text-primary);
            font-size: 17px;
            font-family: inherit;
            cursor: pointer;
            transition: background var(--transition);
            width: 100%;
            text-align: left;
        }}

        .bottom-sheet-btn:active {{
            background: var(--bg-active);
        }}

        .bottom-sheet-btn.danger {{
            color: var(--danger);
        }}

        .bottom-sheet-btn-icon {{
            font-size: 24px;
            width: 32px;
            text-align: center;
        }}

        /* Batch Actions Bar */
        .batch-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--bg-secondary);
            border-top: 0.5px solid var(--border);
            padding: 12px 16px;
            padding-bottom: calc(12px + var(--safe-bottom));
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 150;
            transform: translateY(100%);
            transition: transform 0.3s ease;
        }}

        .batch-bar.active {{
            transform: translateY(0);
        }}

        .batch-info {{
            font-size: 15px;
            color: var(--text-secondary);
        }}

        .batch-actions {{
            display: flex;
            gap: 8px;
        }}

        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 64px 32px;
        }}

        .empty-state-icon {{
            font-size: 64px;
            margin-bottom: 16px;
        }}

        .empty-state-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .empty-state-text {{
            font-size: 15px;
            color: var(--text-secondary);
            max-width: 280px;
            margin: 0 auto;
        }}

        /* Toast Notifications */
        .toast-container {{
            position: fixed;
            top: calc(16px + var(--safe-top));
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
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            font-size: 15px;
            pointer-events: auto;
            animation: slideDown 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .toast-success {{
            border-left: 4px solid var(--success);
        }}

        .toast-error {{
            border-left: 4px solid var(--danger);
        }}

        @keyframes slideDown {{
            from {{
                transform: translateY(-100%);
                opacity: 0;
            }}
            to {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}

        /* Footer */
        .footer {{
            background: var(--bg-secondary);
            border-top: 0.5px solid var(--border);
            padding: 10px 16px;
            padding-bottom: calc(10px + var(--safe-bottom));
            color: var(--text-muted);
            font-size: 13px;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 50;
            transition: transform 0.3s ease;
        }}

        .footer.hidden-by-batch {{
            transform: translateY(100%);
        }}

        .footer-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        /* Preview */
        .preview-container {{
            padding: 16px;
        }}

        .preview-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }}

        .preview-title {{
            font-size: 20px;
            font-weight: 600;
            letter-spacing: -0.4px;
        }}

        .preview-subtitle {{
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 4px;
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
            border-radius: var(--radius);
        }}

        .preview-code {{
            background: var(--bg-secondary);
            border-radius: var(--radius);
            padding: 16px;
            overflow-x: auto;
            font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
            font-size: 15px;
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
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }}

        .modal-overlay.active {{
            opacity: 1;
            visibility: visible;
        }}

        .modal {{
            background: var(--bg-secondary);
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
            padding: 24px;
            padding-bottom: calc(24px + var(--safe-bottom));
            width: 100%;
            max-width: 500px;
            box-shadow: 0 -4px 20px var(--shadow);
            max-height: 80vh;
            overflow-y: auto;
            transform: translateY(100%);
            transition: transform 0.3s ease;
        }}

        .modal-overlay.active .modal {{
            transform: translateY(0);
        }}

        .modal-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
            text-align: center;
        }}

        .modal-actions {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 24px;
        }}

        /* Responsive - Mobile First */
        @media (min-width: 769px) {{
            .file-group {{
                margin: 0;
            }}

            .upload-zone {{
                margin: 12px 0;
            }}

            .flash {{
                margin: 12px 0;
            }}

            .file-item:hover {{
                background: var(--bg-hover);
            }}
        }}

        /* Tablet */
        @media (min-width: 769px) and (max-width: 1024px) {{
            .file-action-btn {{
                opacity: 1;
            }}
        }}

        /* Theme Toggle */
        .theme-toggle {{
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background var(--transition);
        }}

        .theme-toggle:hover, .theme-toggle:active {{
            background: var(--bg-hover);
        }}

        /* Checkbox - iOS style */
        input[type="checkbox"] {{
            display: none;
        }}

        .checkbox-wrapper {{
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            padding: 8px 0;
        }}

        .checkbox-indicator {{
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 2px solid var(--text-muted);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition);
            flex-shrink: 0;
        }}

        .checkbox-wrapper.checked .checkbox-indicator {{
            background: var(--accent);
            border-color: var(--accent);
        }}

        .checkbox-wrapper.checked .checkbox-indicator::after {{
            content: '✓';
            color: white;
            font-size: 14px;
            font-weight: 600;
        }}

        .checkbox-label {{
            font-size: 15px;
            color: var(--text-secondary);
        }}

        /* Loading State */
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

        /* Action Sheet */
        .action-sheet {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--bg-secondary);
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
            padding: 8px;
            padding-bottom: calc(8px + var(--safe-bottom));
            z-index: 300;
            transform: translateY(100%);
            transition: transform 0.3s ease;
        }}

        .action-sheet.active {{
            transform: translateY(0);
        }}

        .action-sheet-group {{
            background: var(--bg-card);
            border-radius: var(--radius);
            overflow: hidden;
            margin-bottom: 8px;
        }}

        .action-sheet-item {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 16px;
            background: transparent;
            border: none;
            border-bottom: 0.5px solid var(--border);
            color: var(--text-primary);
            font-size: 17px;
            font-family: inherit;
            cursor: pointer;
            transition: background var(--transition);
            width: 100%;
        }}

        .action-sheet-item:last-child {{
            border-bottom: none;
        }}

        .action-sheet-item:active {{
            background: var(--bg-active);
        }}

        .action-sheet-item.destructive {{
            color: var(--danger);
        }}

        .action-sheet-cancel {{
            background: var(--bg-card);
            border-radius: var(--radius);
            padding: 16px;
            border: none;
            color: var(--accent);
            font-size: 17px;
            font-weight: 600;
            font-family: inherit;
            cursor: pointer;
            width: 100%;
        }}

        /* Utility */
        .hidden {{
            display: none !important;
        }}

        .text-center {{
            text-align: center;
        }}

        .mt-8 {{
            margin-top: 8px;
        }}

        .mb-8 {{
            margin-bottom: 8px;
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
        metaTheme.content = next === 'light' ? '#f2f2f7' : '#000000';
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
        toast.style.transform = 'translateY(-100%)';
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

// Prevent double tap zoom on iOS
document.addEventListener('touchend', e => {{
    const now = Date.now();
    if (now - (window.lastTouchEnd || 0) < 300) {{
        e.preventDefault();
    }}
    window.lastTouchEnd = now;
}}, false);

// Action sheet management
let currentActionSheet = null;

function showActionSheet(id) {{
    const sheet = document.getElementById(id);
    if (sheet) {{
        sheet.classList.add('active');
        currentActionSheet = sheet;
    }}
}}

function hideActionSheet() {{
    if (currentActionSheet) {{
        currentActionSheet.classList.remove('active');
        currentActionSheet = null;
    }}
}}

// Close action sheet on backdrop click
document.addEventListener('click', function(e) {{
    if (currentActionSheet && !currentActionSheet.contains(e.target)) {{
        hideActionSheet();
    }}
}});
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
