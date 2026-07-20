"""
HTTP request handler for the file server.

Handles all HTTP requests including:
- Directory listing
- File viewing/editing
- File upload/download
- Search
"""

import os
import shutil
import time
import uuid
import hmac
import hashlib
import json
from email.utils import parsedate_to_datetime
import logging
from http.server import BaseHTTPRequestHandler
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs, quote
from pathlib import Path

from . import __version__
from .config import Config
from .security import (
    PathSecurity, RateLimiter, IPFilter,
    SecurityHeaders, get_client_ip
)
from .storage import Storage
from .templates import (
    render_listing, render_editor, render_preview, render_error,
    get_head, get_footer, get_base_html
)
from .utils.mime import guess_mime_type, get_content_disposition
from .utils.format import escape_html

logger = logging.getLogger(__name__)

# Maximum size for form POST bodies (10MB, separate from file uploads)
MAX_FORM_BODY_SIZE = 10 * 1024 * 1024


class FileServerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the file server."""

    # Class-level shared state (set by create_handler_class)
    _config: Config = None
    _rate_limiter: Optional[RateLimiter] = None
    _ip_filter: Optional[IPFilter] = None
    _security_headers: Optional[SecurityHeaders] = None
    _csrf_secret: Optional[bytes] = None

    def __init__(self, *args, **kwargs):
        """Initialize handler with configuration."""
        self.config = self._config
        self.storage = Storage(
            root=self.config.get_root_path(),
            show_hidden=self.config.ui.show_hidden,
        )

        # Reuse class-level shared instances
        self.rate_limiter = self._rate_limiter
        self.ip_filter = self._ip_filter
        self.security_headers = self._security_headers

        # Generate per-request CSRF token (server-secret + client IP + hour window)
        self.csrf_token = self._generate_csrf_token()

        super().__init__(*args, **kwargs)

    def _generate_csrf_token(self) -> str:
        """Generate a stateless CSRF token using HMAC."""
        secret = self._csrf_secret or (self._config.server.host.encode() + str(self._config.server.port).encode())
        # Token valid for ~1 hour windows
        window = str(int(time.time()) // 3600)
        client_ip = self.client_address[0] if hasattr(self, 'client_address') else '0.0.0.0'
        return hmac.new(secret, f"{client_ip}:{window}".encode(), hashlib.sha256).hexdigest()[:32]

    def _validate_csrf_token(self, token: str) -> bool:
        """Validate a CSRF token submitted via POST."""
        if not token:
            return False
        # Accept current window and previous window (for clock skew)
        secret = self._csrf_secret or (self._config.server.host.encode() + str(self._config.server.port).encode())
        client_ip = self.client_address[0]
        for offset in (0, -1):
            window = str((int(time.time()) // 3600) + offset)
            expected = hmac.new(secret, f"{client_ip}:{window}".encode(), hashlib.sha256).hexdigest()[:32]
            if hmac.compare_digest(token, expected):
                return True
        return False

    def setup(self):
        """Set up the handler."""
        super().setup()
        self.request_id = str(uuid.uuid4())[:8]
        self.start_time = time.time()

    def log_message(self, format, *args):
        """Log request with custom format."""
        logger.info(
            f"[{self.request_id}] {self.address_string()} - {format % args}",
            extra={
                'request_id': self.request_id,
                'client_ip': self.client_address[0],
                'method': self.command,
                'path': self.path,
            }
        )

    def _send_response(
        self,
        status: int,
        body: bytes,
        content_type: str = "text/html; charset=utf-8",
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        """Send HTTP response with security headers."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("X-Request-ID", self.request_id)

        # Add security headers
        for key, value in self.security_headers.get_headers().items():
            self.send_header(key, value)

        # Add custom headers
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)

        self.end_headers()

        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_file_stream(
        self,
        file_path: Path,
        content_type: str,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        """Send a file as a streaming response (avoids loading into memory)."""
        stat = file_path.stat()
        file_size = stat.st_size

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Last-Modified", time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stat.st_mtime)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("X-Request-ID", self.request_id)

        for key, value in self.security_headers.get_headers().items():
            self.send_header(key, value)

        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)

        self.end_headers()

        if self.command == "HEAD":
            return

        try:
            with open(file_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
        except (OSError, PermissionError) as e:
            logger.exception(f"Error streaming file: {e}")

    def _send_html(self, status: int, html: str, title: str = "File Server"):
        """Send HTML response wrapped in base template."""
        full_html = get_base_html(title, html, self.config.ui.theme)
        self._send_response(status, full_html.encode("utf-8"))

    def _send_error(self, status: int, message: str, details: Optional[str] = None):
        """Send error response."""
        html = render_error(status, message, details, self.request_id)
        self._send_html(status, html, f"Error {status}")

    def _send_redirect(self, location: str, status: int = 303):
        """Send redirect response."""
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("X-Request-ID", self.request_id)
        self.end_headers()

    def _check_rate_limit(self) -> bool:
        """Check rate limit for client."""
        if not self.rate_limiter:
            return True

        client_ip = get_client_ip(self)
        allowed, retry_after = self.rate_limiter.is_allowed(client_ip)

        if not allowed:
            self.send_response(429)
            self.send_header("Retry-After", str(retry_after))
            self.send_header("X-Request-ID", self.request_id)
            self.end_headers()
            return False

        return True

    def _check_ip_filter(self) -> bool:
        """Check if client IP is allowed."""
        client_ip = get_client_ip(self)
        return self.ip_filter.is_allowed(client_ip)

    def _get_query_params(self) -> Dict[str, str]:
        """Get query parameters as dictionary."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        return {k: v[0] if v else "" for k, v in params.items()}

    def _get_form_data(self) -> Dict[str, str]:
        """Get form data from POST request with body size limit."""
        content_type = self.headers.get("Content-Type", "")

        if content_type.startswith("application/x-www-form-urlencoded"):
            # Use buffered body if available (from CSRF validation)
            if hasattr(self, '_buffered_body') and self._buffered_body:
                params = parse_qs(self._buffered_body.decode('utf-8'))
                return {k: v[0] if v else "" for k, v in params.items()}

            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > MAX_FORM_BODY_SIZE:
                raise ValueError(f"Request body too large: {content_length} bytes (max {MAX_FORM_BODY_SIZE})")
            body = self.rfile.read(content_length).decode("utf-8")
            params = parse_qs(body)
            return {k: v[0] if v else "" for k, v in params.items()}

        return {}

    def _get_multipart_data(self) -> Tuple[Dict[str, str], Dict[str, Tuple[str, bytes]]]:
        """Get multipart form data with body size limit."""
        content_type = self.headers.get("Content-Type", "")

        if not content_type.startswith("multipart/form-data"):
            return {}, {}

        # Extract boundary
        boundary = content_type.split("boundary=", 1)[1].strip().strip('"')
        if not boundary:
            return {}, {}

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > self.config.server.max_upload_size:
            raise ValueError(f"Upload too large: {content_length} bytes (max {self.config.server.max_upload_size})")
        body = self.rfile.read(content_length)

        fields = {}
        files = {}

        parts = body.split(f"--{boundary}".encode())
        for part in parts:
            part = part.strip(b"\r\n")
            if not part or part == b"--":
                continue

            # Split headers and body
            header_end = part.find(b"\r\n\r\n")
            if header_end == -1:
                continue

            header_data = part[:header_end]
            file_data = part[header_end + 4:].rstrip(b"\r\n")

            # Parse headers
            headers = {}
            for line in header_data.decode("utf-8", errors="replace").split("\r\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

            # Get content disposition
            disposition = headers.get("content-disposition", "")
            if not disposition:
                continue

            # Extract name
            name_match = None
            for item in disposition.split(";"):
                item = item.strip()
                if item.startswith("name="):
                    name_match = item[5:].strip('"')
                    break

            if not name_match:
                continue

            # Check if it's a file
            filename_match = None
            for item in disposition.split(";"):
                item = item.strip()
                if item.startswith("filename="):
                    filename_match = item[9:].strip('"')
                    break

            if filename_match:
                files[name_match] = (filename_match, file_data)
            else:
                fields[name_match] = file_data.decode("utf-8", errors="replace")

        return fields, files

    def do_GET(self):
        """Handle GET requests."""
        try:
            # Check rate limit
            if not self._check_rate_limit():
                return

            # Check IP filter
            if not self._check_ip_filter():
                self._send_error(403, "Access denied")
                return

            # Parse request
            parsed = urlparse(self.path)
            path = parsed.path
            params = self._get_query_params()

            # Route request
            if path == "/" or path == "":
                self._handle_root(params)
            elif path == "/raw":
                self._handle_raw(params)
            elif path == "/search":
                self._handle_search(params)
            elif path == "/download":
                self._handle_download(params)
            elif path == "/api/files":
                self._handle_api_files(params)
            elif path == "/health":
                self._handle_health()
            else:
                self._send_error(404, "Not found")

        except ValueError as e:
            self._send_error(400, str(e))
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            self._send_error(500, "Internal server error", str(e))

    def do_POST(self):
        """Handle POST requests."""
        try:
            # Check rate limit
            if not self._check_rate_limit():
                return

            # Check IP filter
            if not self._check_ip_filter():
                self._send_error(403, "Access denied")
                return

            # Validate CSRF token
            if not self._validate_post_csrf():
                self._send_error(403, "CSRF validation failed. Please refresh the page and try again.")
                return

            # Parse request
            parsed = urlparse(self.path)
            path = parsed.path

            # Route request
            if path == "/save":
                self._handle_save()
            elif path == "/upload":
                self._handle_upload()
            elif path == "/mkdir":
                self._handle_mkdir()
            elif path == "/delete":
                self._handle_delete_post()
            elif path == "/move":
                self._handle_move()
            elif path == "/copy":
                self._handle_copy()
            elif path == "/download-selected":
                self._handle_download_selected()
            else:
                self._send_error(404, "Not found")

        except ValueError as e:
            self._send_error(400, str(e))
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            self._send_error(500, "Internal server error", str(e))

    def _validate_post_csrf(self) -> bool:
        """Validate CSRF protection on POST requests.

        Strategy: Check the Origin/Referer header to ensure the request
        comes from the same host. This prevents cross-site request forgery
        without requiring token state on the server.
        """
        origin = self.headers.get('Origin')
        referer = self.headers.get('Referer')

        # Build expected origin
        scheme = 'https' if self.config.security.ssl.enabled else 'http'
        host = self.headers.get('Host', f'{self.config.server.host}:{self.config.server.port}')
        expected_origin = f'{scheme}://{host}'

        if origin:
            # Origin header present — must match our host
            if origin != expected_origin:
                return False

        elif referer:
            # Referer header present — must start with our origin
            if not referer.startswith(expected_origin):
                return False

        # For multipart/form-data (file uploads), we rely on Origin/Referer only
        # since reading the body to get the token would consume the stream.
        # We also buffer the form body for form-urlencoded so downstream handlers
        # can still read it.
        content_type = self.headers.get('Content-Type', '')
        if content_type.startswith('multipart/form-data'):
            return True

        if content_type.startswith('application/x-www-form-urlencoded'):
            try:
                # Read and buffer the body so it can be re-read by handlers
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0 and content_length <= MAX_FORM_BODY_SIZE:
                    raw_body = self.rfile.read(content_length)
                    self._buffered_body = raw_body
                    params = parse_qs(raw_body.decode('utf-8'))
                    form = {k: v[0] if v else '' for k, v in params.items()}
                    token = form.get('_csrf', '')
                    if token and not self._validate_csrf_token(token):
                        return False
            except Exception:
                logger.warning("Error validating CSRF token", exc_info=True)

        return True

    def do_HEAD(self):
        """Handle HEAD requests."""
        self.do_GET()

    def _handle_root(self, params: Dict[str, str]):
        """Handle root path request."""
        rel_path = params.get("p", "")
        sort_by = params.get("sort", self.config.ui.default_sort)
        show_hidden = params.get("hidden", "1" if self.config.ui.show_hidden else "0") == "1"
        try:
            page = int(params.get("page", "1"))
        except ValueError:
            page = 1

        # Check if edit mode
        if "edit" in params and rel_path and not rel_path.endswith("/"):
            self._handle_editor(params)
            return

        # Check if preview mode
        if "preview" in params and rel_path and not rel_path.endswith("/"):
            self._handle_preview(params)
            return

        # Build path
        try:
            target = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        if not target.exists():
            self._send_error(404, f"Path not found: {escape_html(rel_path)}")
            return

        if target.is_file():
            # Show preview for files
            self._handle_preview(params)
            return

        # List directory
        files = self.storage.list_directory(target, sort_by=sort_by, show_hidden=show_hidden)

        # Pagination
        per_page = self.config.ui.items_per_page
        total_pages = max(1, (len(files) + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_files = files[start_idx:end_idx]

        # Render listing
        html = render_listing(
            files=page_files,
            current_path=rel_path,
            sort_by=sort_by,
            show_hidden=show_hidden,
            page=page,
            total_pages=total_pages,
            csrf_token=self.csrf_token,
            features={
                "upload": self.config.features.upload,
                "delete": self.config.features.delete,
                "mkdir": self.config.features.mkdir,
                "edit": self.config.features.edit,
                "search": self.config.features.search,
            },
        )

        self._send_html(200, html, f"/{escape_html(rel_path)}" if rel_path else "Home")

    def _handle_editor(self, params: Dict[str, str]):
        """Handle file editor request."""
        rel_path = params.get("p", "")

        try:
            target = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        if not target.exists():
            self._send_error(404, f"File not found: {escape_html(rel_path)}")
            return

        if not target.is_file():
            self._send_error(400, "Not a file")
            return

        # Read file content
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error reading file: {e}")
            return

        # Render editor
        html = render_editor(
            file_path=rel_path,
            content=content,
            csrf_token=self.csrf_token,
        )

        self._send_html(200, html, f"Edit: {escape_html(rel_path)}")

    def _handle_preview(self, params: Dict[str, str]):
        """Handle file preview request."""
        rel_path = params.get("p", "")

        try:
            target = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        if not target.exists():
            self._send_error(404, f"File not found: {escape_html(rel_path)}")
            return

        if not target.is_file():
            self._send_error(400, "Not a file")
            return

        # Get file info
        stat = target.stat()
        mime_type = guess_mime_type(target.name)
        is_text = self.storage.is_text_file(target)

        # Read content for text files
        content = None
        if is_text:
            try:
                content = target.read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError, UnicodeDecodeError):
                logger.warning(f"Could not read file content for preview: {rel_path}")

        # Render preview
        html = render_preview(
            file_path=rel_path,
            file_name=target.name,
            mime_type=mime_type,
            file_size=stat.st_size,
            content=content,
            is_text=is_text,
            csrf_token=self.csrf_token,
        )

        self._send_html(200, html, escape_html(target.name))

    def _handle_raw(self, params: Dict[str, str]):
        """Handle raw file download."""
        rel_path = params.get("p", "")

        try:
            target = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        if not target.exists():
            self._send_error(404, f"File not found: {escape_html(rel_path)}")
            return

        if not target.is_file():
            self._send_error(400, "Not a file")
            return

        # Get file info
        stat = target.stat()
        mime_type = guess_mime_type(target.name) or "application/octet-stream"
        last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stat.st_mtime))

        # Check If-Modified-Since for conditional requests
        if_modified_since = self.headers.get('If-Modified-Since')
        if if_modified_since:
            try:
                ims_dt = parsedate_to_datetime(if_modified_since)
                if ims_dt.timestamp() >= stat.st_mtime:
                    self.send_response(304)
                    self.send_header("Last-Modified", last_modified)
                    self.send_header("X-Request-ID", self.request_id)
                    self.end_headers()
                    return
            except (ValueError, TypeError, OverflowError):
                pass

        # Set headers
        extra_headers = {
            "Content-Disposition": get_content_disposition(target.name, mime_type),
            "Content-Length": str(stat.st_size),
            "Last-Modified": last_modified,
        }

        # Send file using streaming to avoid loading into memory
        try:
            self._send_file_stream(target, mime_type, extra_headers)
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error reading file: {e}")

    def _handle_search(self, params: Dict[str, str]):
        """Handle search request."""
        query = params.get("q", "")
        rel_path = params.get("p", "")
        show_hidden = params.get("hidden", "1" if self.config.ui.show_hidden else "0") == "1"

        if not query:
            self._send_redirect(f"/?p={quote(rel_path)}")
            return

        # Build search path
        try:
            search_path = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        # Search
        results = self.storage.search(query, search_path, show_hidden=show_hidden)

        # Render results
        html = render_listing(
            files=results,
            current_path=rel_path,
            search_query=query,
            sort_by="name",
            show_hidden=show_hidden,
            flash_message=f"Found {len(results)} results for '{escape_html(query)}'",
            flash_type="info",
            csrf_token=self.csrf_token,
            features={
                "upload": self.config.features.upload,
                "delete": self.config.features.delete,
                "mkdir": self.config.features.mkdir,
                "edit": self.config.features.edit,
                "search": self.config.features.search,
            },
        )

        self._send_html(200, html, f"Search: {escape_html(query)}")

    def _handle_download(self, params: Dict[str, str]):
        """Handle folder download as ZIP."""
        if not self.config.features.download_zip:
            self._send_error(403, "Downloads disabled")
            return

        rel_path = params.get("p", "")

        try:
            target = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        if not target.exists():
            self._send_error(404, f"Path not found: {escape_html(rel_path)}")
            return

        # Create ZIP
        zip_content = self.storage.create_zip([target])
        if not zip_content:
            self._send_error(500, "Error creating ZIP")
            return

        # Send ZIP
        filename = f"{target.name}.zip"
        extra_headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(zip_content)),
        }

        self._send_response(200, zip_content, "application/zip", extra_headers)

    def _handle_api_files(self, params: Dict[str, str]):
        """Handle API file listing request."""
        rel_path = params.get("p", "")
        sort_by = params.get("sort", "name")

        try:
            target = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        if not target.is_dir():
            self._send_error(400, "Not a directory")
            return

        # List files
        files = self.storage.list_directory(target, sort_by=sort_by)

        # Convert to JSON
        data = [f.to_dict() for f in files]

        self._send_response(
            200,
            json.dumps(data).encode("utf-8"),
            "application/json",
        )

    def _handle_health(self):
        """Handle health check request."""
        data = {
            "status": "healthy",
            "version": __version__,
            "uptime": time.time() - self.start_time,
        }
        self._send_response(200, json.dumps(data).encode("utf-8"), "application/json")

    def _handle_save(self):
        """Handle file save request."""
        if not self.config.features.edit:
            self._send_error(403, "Editing disabled")
            return

        # Get form data
        form = self._get_form_data()
        rel_path = form.get("p", "")
        content = form.get("content", "")

        try:
            target = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        # Save file
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

            # Redirect back to editor
            self._send_redirect(f"/?p={quote(rel_path)}&edit=1&saved=1")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error saving file: {e}")

    def _handle_upload(self):
        """Handle file upload request."""
        if not self.config.features.upload:
            self._send_error(403, "Uploads disabled")
            return

        # Get multipart data
        fields, files = self._get_multipart_data()
        rel_path = fields.get("p", "")

        if not files:
            self._send_redirect(f"/?p={quote(rel_path)}&error=no_files")
            return

        # Build target directory
        try:
            target_dir = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        target_dir.mkdir(parents=True, exist_ok=True)

        # Save files
        saved = []
        for field_name, (filename, data) in files.items():
            # Sanitize filename
            safe_name = PathSecurity.sanitize_filename(filename)
            if not safe_name:
                continue

            # Check file size
            if len(data) > self.config.server.max_upload_size:
                continue

            # Save file
            target_file = target_dir / safe_name
            # Avoid overwriting existing files
            if target_file.exists():
                stem = target_file.stem
                suffix = target_file.suffix
                counter = 1
                while True:
                    new_name = f"{stem}_{counter}{suffix}"
                    candidate = target_dir / new_name
                    if not candidate.exists():
                        target_file = candidate
                        safe_name = new_name
                        break
                    counter += 1
            try:
                target_file.write_bytes(data)
                saved.append(safe_name)
            except (OSError, PermissionError) as e:
                logger.exception(f"Error saving file {safe_name}: {e}")

        # Redirect
        if saved:
            msg = f"Uploaded: {', '.join(saved)}"
            self._send_redirect(f"/?p={quote(rel_path)}&success={quote(msg)}")
        else:
            self._send_redirect(f"/?p={quote(rel_path)}&error=upload_failed")

    def _handle_mkdir(self):
        """Handle directory creation request."""
        if not self.config.features.mkdir:
            self._send_error(403, "Directory creation disabled")
            return

        # Get form data
        form = self._get_form_data()
        rel_path = form.get("p", "")
        dir_name = form.get("name", "").strip()

        if not dir_name:
            self._send_error(400, "Directory name required")
            return

        # Validate directory name
        if "/" in dir_name or "\\" in dir_name or ".." in dir_name:
            self._send_error(400, "Invalid directory name")
            return

        # Build target path
        try:
            target = PathSecurity.safe_join(
                self.config.get_root_path(),
                f"{rel_path}/{dir_name}" if rel_path else dir_name
            )
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        # Create directory
        try:
            target.mkdir(parents=True, exist_ok=True)
            self._send_redirect(f"/?p={quote(str(target.relative_to(self.config.get_root_path())))}")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error creating directory: {e}")

    def _handle_delete_post(self):
        """Handle file/directory deletion via POST."""
        if not self.config.features.delete:
            self._send_error(403, "Deletion disabled")
            return

        # Get form data
        form = self._get_form_data()
        rel_path = form.get("p", "")

        try:
            target = PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        if not target.exists():
            self._send_error(404, "Path not found")
            return

        # Delete
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

            logger.info(f"[{self.request_id}] Deleted: {rel_path}")

            # Redirect to parent
            parent = str(target.parent.relative_to(self.config.get_root_path()))
            self._send_redirect(f"/?p={quote(parent)}")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error deleting: {e}")

    def _handle_move(self):
        """Handle file/directory move request."""
        if not self.config.features.move:
            self._send_error(403, "Move disabled")
            return

        # Get form data
        form = self._get_form_data()
        source = form.get("source", "")
        destination = form.get("destination", "")

        try:
            source_path = PathSecurity.safe_join(self.config.get_root_path(), source)
            dest_path = PathSecurity.safe_join(self.config.get_root_path(), destination)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        if not source_path.exists():
            self._send_error(404, "Source not found")
            return

        # Move
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_path))

            logger.info(f"[{self.request_id}] Moved: {source} -> {destination}")

            # Redirect
            parent = str(dest_path.parent.relative_to(self.config.get_root_path()))
            self._send_redirect(f"/?p={quote(parent)}")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error moving: {e}")

    def _handle_copy(self):
        """Handle file/directory copy request."""
        if not self.config.features.copy:
            self._send_error(403, "Copy disabled")
            return

        # Get form data
        form = self._get_form_data()
        source = form.get("source", "")
        destination = form.get("destination", "")

        try:
            source_path = PathSecurity.safe_join(self.config.get_root_path(), source)
            dest_path = PathSecurity.safe_join(self.config.get_root_path(), destination)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return

        if not source_path.exists():
            self._send_error(404, "Source not found")
            return

        # Copy
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path.is_dir():
                shutil.copytree(str(source_path), str(dest_path))
            else:
                shutil.copy2(str(source_path), str(dest_path))

            logger.info(f"[{self.request_id}] Copied: {source} -> {destination}")

            # Redirect
            parent = str(dest_path.parent.relative_to(self.config.get_root_path()))
            self._send_redirect(f"/?p={quote(parent)}")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error copying: {e}")

    def _handle_download_selected(self):
        """Handle download of selected files/folders as ZIP."""
        if not self.config.features.download_zip:
            self._send_error(403, "Downloads disabled")
            return

        # Get form data (use buffered body from CSRF validation if available)
        if hasattr(self, '_buffered_body') and self._buffered_body:
            body = self._buffered_body.decode('utf-8')
        else:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > MAX_FORM_BODY_SIZE:
                self._send_error(400, "Request body too large")
                return
            body = self.rfile.read(content_length).decode("utf-8")
        params = parse_qs(body)

        current_path = params.get("p", [""])[0]
        selected_files = params.get("files", [])

        if not selected_files:
            self._send_error(400, "No files selected")
            return

        # Build list of paths to zip
        paths = []
        for file_path in selected_files:
            try:
                target = PathSecurity.safe_join(self.config.get_root_path(), file_path)
                if target.exists():
                    paths.append(target)
            except ValueError:
                logger.warning(f"Skipping invalid path in download selection: {file_path}")
                continue

        if not paths:
            self._send_error(404, "No valid files found")
            return

        # Create ZIP
        zip_content = self.storage.create_zip(paths)
        if not zip_content:
            self._send_error(500, "Error creating ZIP")
            return

        # Determine filename
        if len(paths) == 1:
            filename = f"{paths[0].name}.zip"
        else:
            folder_name = current_path.split("/")[-1] if current_path else "files"
            filename = f"{folder_name}_selected.zip"

        # Send ZIP
        extra_headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(zip_content)),
        }

        self._send_response(200, zip_content, "application/zip", extra_headers)


def create_handler_class(config: Config):
    """Create a handler class with configuration.

    Shared security objects (RateLimiter, IPFilter, SecurityHeaders) are
    created once at the class level so their state (e.g., rate limit buckets)
    persists across requests.
    """
    # Create shared instances (persist across requests)
    rate_limiter = RateLimiter(
        requests_per_minute=config.security.rate_limit.requests_per_minute,
        burst=config.security.rate_limit.burst,
    ) if config.security.rate_limit.enabled else None

    ip_filter = IPFilter(
        allowed_ips=config.security.allowed_ips,
        blocked_ips=config.security.blocked_ips,
    )

    security_headers = SecurityHeaders()

    # Generate CSRF secret (random, overridable via env var)
    csrf_secret_str = os.environ.get('FILESERVER_CSRF_SECRET')
    if csrf_secret_str:
        csrf_secret = bytes.fromhex(csrf_secret_str)
    else:
        csrf_secret = os.urandom(32)

    class ConfiguredHandler(FileServerHandler):
        # Class-level shared state
        _config = config
        _rate_limiter = rate_limiter
        _ip_filter = ip_filter
        _security_headers = security_headers
        _csrf_secret = csrf_secret
    return ConfiguredHandler
