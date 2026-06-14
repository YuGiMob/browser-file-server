"""
Error page template with professional mobile-app design.
"""

from typing import Optional
from ..utils.format import escape_html as _escape_html


def render_error(
    status_code: int,
    message: str,
    details: Optional[str] = None,
    request_id: Optional[str] = None,
) -> str:
    """
    Render error page HTML.

    Args:
        status_code: HTTP status code
        message: Error message
        details: Additional details
        request_id: Request ID for tracking

    Returns:
        HTML string
    """
    icon = _get_error_icon(status_code)
    title = _get_error_title(status_code)

    details_html = ""
    if details:
        details_html = f"""
        <div style="margin-top: 24px; padding: 16px; background: var(--bg-tertiary); border-radius: var(--radius); text-align: left;">
            <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word; font-size: 13px; color: var(--text-secondary);">{_escape_html(details)}</pre>
        </div>"""

    request_id_html = ""
    if request_id:
        request_id_html = f"""
        <div style="margin-top: 16px; color: var(--text-muted); font-size: 13px;">
            Request ID: {request_id}
        </div>"""

    html = f"""
<div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 32px;">
    <div style="text-align: center; max-width: 400px;">
        <div style="font-size: 80px; margin-bottom: 24px;">{icon}</div>
        <h1 style="font-size: 48px; font-weight: 700; margin-bottom: 8px; letter-spacing: -1px;">{status_code}</h1>
        <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 16px; letter-spacing: -0.4px;">{title}</h2>
        <p style="color: var(--text-secondary); margin-bottom: 32px; line-height: 1.5; font-size: 17px;">{message}</p>
        
        {details_html}
        {request_id_html}
        
        <div style="margin-top: 40px; display: flex; flex-direction: column; gap: 12px;">
            <a href="/" class="btn" style="width: 100%;">Go Home</a>
            <button class="btn btn-ghost" style="width: 100%;" onclick="window.history.back()">Go Back</button>
        </div>
    </div>
</div>

<script>
// Auto-refresh for server errors
if ({status_code} >= 500) {{
    let countdown = 30;
    const timer = setInterval(() => {{
        countdown--;
        if (countdown <= 0) {{
            clearInterval(timer);
            window.location.reload();
        }}
    }}, 1000);
}}
</script>
"""

    return html

def _get_error_icon(status_code: int) -> str:
    """Get icon for error status code."""
    icons = {
        400: "⚠️",
        401: "🔒",
        403: "🚫",
        404: "🔍",
        405: "⚠️",
        408: "⏰",
        413: "📦",
        429: "🐢",
        500: "💥",
        502: "🔌",
        503: "🔧",
        504: "⏰",
    }
    return icons.get(status_code, "⚠️")


def _get_error_title(status_code: int) -> str:
    """Get title for error status code."""
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        408: "Request Timeout",
        413: "File Too Large",
        429: "Too Many Requests",
        500: "Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }
    return titles.get(status_code, "Error")
