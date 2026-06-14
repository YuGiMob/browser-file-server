"""
Error page template.
"""

from typing import Optional


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
        <div style="margin-top: 16px; padding: 12px; background: var(--bg-tertiary); border-radius: var(--radius); text-align: left;">
            <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word; font-size: 12px;">{details}</pre>
        </div>"""

    request_id_html = ""
    if request_id:
        request_id_html = f"""
        <div style="margin-top: 8px; color: var(--text-muted); font-size: 11px;">
            Request ID: {request_id}
        </div>"""

    html = f"""
<div style="display: flex; align-items: center; justify-content: center; min-height: 80vh; padding: 32px;">
    <div style="text-align: center; max-width: 500px;">
        <div style="font-size: 72px; margin-bottom: 16px;">{icon}</div>
        <h1 style="font-size: 36px; margin-bottom: 8px; color: var(--text-primary);">{status_code}</h1>
        <h2 style="font-size: 20px; margin-bottom: 16px; color: var(--text-secondary); font-weight: normal;">{title}</h2>
        <p style="color: var(--text-secondary); margin-bottom: 24px; line-height: 1.6;">{message}</p>
        
        {details_html}
        {request_id_html}
        
        <div style="margin-top: 32px; display: flex; justify-content: center; gap: 12px;">
            <a href="/" class="btn">🏠 Go Home</a>
            <button class="btn btn-outline" onclick="window.history.back()">← Go Back</button>
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


def render_not_found(path: str) -> str:
    """
    Render 404 not found page.

    Args:
        path: Requested path

    Returns:
        HTML string
    """
    return render_error(
        status_code=404,
        message=f"The requested path <code>{path}</code> was not found on this server.",
        details=None,
    )


def render_forbidden(path: str) -> str:
    """
    Render 403 forbidden page.

    Args:
        path: Requested path

    Returns:
        HTML string
    """
    return render_error(
        status_code=403,
        message=f"You don't have permission to access <code>{path}</code>.",
        details=None,
    )


def render_internal_error(error: Exception, request_id: Optional[str] = None) -> str:
    """
    Render 500 internal error page.

    Args:
        error: Exception object
        request_id: Request ID

    Returns:
        HTML string
    """
    import traceback

    details = None
    try:
        details = traceback.format_exc()
    except:
        pass

    return render_error(
        status_code=500,
        message="An internal server error occurred. Please try again later.",
        details=details,
        request_id=request_id,
    )


def _get_error_icon(status_code: int) -> str:
    """Get icon for error status code."""
    icons = {
        400: "❌",
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
    return icons.get(status_code, "❌")


def _get_error_title(status_code: int) -> str:
    """Get title for error status code."""
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        408: "Request Timeout",
        413: "Payload Too Large",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }
    return titles.get(status_code, "Error")
