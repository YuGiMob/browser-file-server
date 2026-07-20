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
import tempfile
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

from . import __version__, ROOT, RAW, SEARCH, DOWNLOAD, API_FILES, HEALTH, SAVE, UPLOAD, MKDIR, DELETE, MOVE, COPY, DOWNLOAD_SELECTED
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

MAX_FORM_BODY_SIZE = 10 * 1024 * 1024


class FileServerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the file server."""

    _config: Config = None
    _rate_limiter: Optional[RateLimiter] = None
    _ip_filter: Optional[IPFilter] = None
    _security_headers: Optional[SecurityHeaders] = None
    _csrf_secret: Optional[bytes] = None

    def __init__(self, *args, **kwargs):
        self.config = self._config
        self.storage = Storage(
            root=self.config.get_root_path(),
            show_hidden=self.config.ui.show_hidden,
        )
        self.rate_limiter = self._rate_limiter
        self.ip_filter = self._ip_filter
        self.security_headers = self._security_headers
        self.csrf_token = self._generate_csrf_token()
        super().__init__(*args, **kwargs)

    def _get_csrf_secret(self) -> bytes:
        return self._csrf_secret

    def _generate_csrf_token(self) -> str:
        secret = self._get_csrf_secret()
        window = str(int(time.time()) // 3600)
        client_ip = self.client_address[0] if hasattr(self, 'client_address') else '0.0.0.0'
        return hmac.new(secret, f"{client_ip}:{window}".encode(), hashlib.sha256).hexdigest()[:32]

    def _validate_csrf_token(self, token: str) -> bool:
        if not token:
            return False
        secret = self._get_csrf_secret()
        client_ip = get_client_ip(self)
        for offset in (0, -1):
            window = str((int(time.time()) // 3600) + offset)
            expected = hmac.new(secret, f"{client_ip}:{window}".encode(), hashlib.sha256).hexdigest()[:32]
            if hmac.compare_digest(token, expected):
                return True
        return False

    def _extract_csrf_from_multipart(self, body: bytes) -> str:
        csrf_marker = b'name="_csrf"'
        idx = body.find(csrf_marker)
        if idx == -1:
            return ''
        header_end = body.find(b'\r\n\r\n', idx)
        if header_end == -1:
            return ''
        value_start = header_end + 4
        value_end = body.find(b'\r\n', value_start)
        if value_end == -1:
            return ''
        return body[value_start:value_end].decode('utf-8').strip()

    def setup(self):
        super().setup()
        self.request_id = str(uuid.uuid4())[:8]
        self.start_time = time.time()

    def log_message(self, format, *args):
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
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("X-Request-ID", self.request_id)

        for key, value in self.security_headers.get_headers().items():
            self.send_header(key, value)

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
        stat = file_path.stat()
        file_size = stat.st_size

        range_header = self.headers.get('Range', '')
        if range_header and range_header.startswith('bytes='):
            ranges = []
            for part in range_header[6:].split(','):
                part = part.strip()
                if '-' in part:
                    start_str, end_str = part.split('-', 1)
                    start_str = start_str.strip()
                    end_str = end_str.strip()
                    if start_str:
                        start = int(start_str)
                        end = int(end_str) if end_str else file_size - 1
                    else:
                        suffix = int(end_str)
                        start = max(0, file_size - suffix)
                        end = file_size - 1
                    if start > end or start >= file_size:
                        self.send_response(416)
                        self.send_header('Content-Range', f'bytes */{file_size}')
                        self.send_header('X-Request-ID', self.request_id)
                        self.end_headers()
                        return
                    end = min(end, file_size - 1)
                    ranges.append((start, end))
            if ranges:
                start, end = ranges[0]
                content_length = end - start + 1
                self.send_response(206)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(content_length))
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Last-Modified', time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(stat.st_mtime)))
                self.send_header('Cache-Control', 'private, max-age=3600')
                self.send_header('X-Request-ID', self.request_id)
                for key, value in self.security_headers.get_headers().items():
                    self.send_header(key, value)
                if extra_headers:
                    for key, value in extra_headers.items():
                        if key not in ('Content-Length', 'Content-Range'):
                            self.send_header(key, value)
                self.end_headers()
                if self.command == 'HEAD':
                    return
                try:
                    with open(file_path, 'rb') as f:
                        f.seek(start)
                        remaining = content_length
                        while remaining > 0:
                            chunk_size = min(65536, remaining)
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                except (OSError, PermissionError) as e:
                    logger.exception(f'Error streaming file: {e}')
                return

        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(file_size))
        self.send_header('Last-Modified', time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(stat.st_mtime)))
        self.send_header('Cache-Control', 'private, max-age=3600')
        self.send_header('X-Request-ID', self.request_id)

        for key, value in self.security_headers.get_headers().items():
            self.send_header(key, value)

        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)

        self.end_headers()

        if self.command == 'HEAD':
            return

        try:
            with open(file_path, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        except (OSError, PermissionError) as e:
            logger.exception(f'Error streaming file: {e}')

    def _send_html(self, status: int, html: str, title: str = "File Server"):
        full_html = get_base_html(title, html, self.config.ui.theme)
        self._send_response(status, full_html.encode("utf-8"))

    def _send_error(self, status: int, message: str, details: Optional[str] = None):
        html = render_error(status, message, details, self.request_id)
        self._send_html(status, html, f"Error {status}")

    def _send_redirect(self, location: str, status: int = 303):
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("X-Request-ID", self.request_id)
        self.end_headers()

    def _resolve_path(self, rel_path: str) -> Optional[Path]:
        try:
            return PathSecurity.safe_join(self.config.get_root_path(), rel_path)
        except ValueError as e:
            self._send_error(400, f"Invalid path: {e}")
            return None

    def _check_feature(self, attr: str, label: str) -> bool:
        if not getattr(self.config.features, attr, True):
            self._send_error(403, f"{label} disabled")
            return False
        return True

    def _check_rate_limit(self) -> bool:
        if not self.rate_limiter:
            return True

        if not hasattr(self.__class__, '_request_count'):
            self.__class__._request_count = 0
        self.__class__._request_count += 1
        if self.__class__._request_count % 100 == 0:
            self.rate_limiter.cleanup()

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
        client_ip = get_client_ip(self)
        return self.ip_filter.is_allowed(client_ip)

    def _get_query_params(self) -> Dict[str, str]:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        return {k: v[0] if v else "" for k, v in params.items()}

    def _get_form_data(self) -> Dict[str, str]:
        content_type = self.headers.get("Content-Type", "")
        if content_type.startswith("application/x-www-form-urlencoded"):
            if hasattr(self, '_buffered_body') and self._buffered_body:
                params = parse_qs(self._buffered_body.decode('utf-8'))
                return {k: v[0] if v else "" for k, v in params.items()}
        return {}

    def _get_multipart_data(self) -> Tuple[Dict[str, str], Dict[str, Tuple[str, bytes]]]:
        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            return {}, {}

        boundary = content_type.split('boundary=', 1)[1].strip().strip('"')
        if not boundary:
            return {}, {}

        if not hasattr(self, '_buffered_body') or not self._buffered_body:
            return {}, {}

        body = self._buffered_body

        if len(body) > self.config.server.max_upload_size:
            raise ValueError(f'Upload too large: {len(body)} bytes (max {self.config.server.max_upload_size})')

        fields = {}
        files = {}

        boundary_bytes = f'--{boundary}'.encode()
        boundary_end = f'--{boundary}--'.encode()

        parts = []
        pos = 0
        while True:
            if pos == 0 and body.startswith(boundary_bytes):
                idx = 0
            else:
                idx = body.find(b'\r\n' + boundary_bytes, pos)
                if idx == -1:
                    break
                idx += 2
            if body[idx:].startswith(boundary_end):
                break
            part_start = idx + len(boundary_bytes)
            next_idx = body.find(b'\r\n' + boundary_bytes, part_start)
            if next_idx == -1:
                part_data = body[part_start:]
                parts.append(part_data)
                break
            else:
                part_data = body[part_start:next_idx]
                parts.append(part_data)
                pos = next_idx

        for part in parts:
            part = part.strip(b'\r\n')
            if not part:
                continue

            header_end = part.find(b'\r\n\r\n')
            if header_end == -1:
                continue

            header_data = part[:header_end]
            file_data = part[header_end + 4:]

            headers = {}
            for line in header_data.decode('utf-8', errors='replace').split('\r\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            disposition = headers.get('content-disposition', '')
            if not disposition:
                continue

            name = None
            filename = None
            for item in disposition.split(';'):
                item = item.strip()
                if item.startswith('name='):
                    name = item[5:].strip('"')
                elif item.startswith('filename='):
                    filename = item[9:].strip('"')

            if not name:
                continue

            if filename:
                files[name] = (filename, file_data)
            else:
                fields[name] = file_data.decode('utf-8', errors='replace')

        return fields, files

    def do_GET(self):
        try:
            if not self._check_rate_limit():
                return

            if not self._check_ip_filter():
                self._send_error(403, "Access denied")
                return

            parsed = urlparse(self.path)
            path = parsed.path
            params = self._get_query_params()

            if path == ROOT or path == "":
                self._handle_root(params)
            elif path == RAW:
                self._handle_raw(params)
            elif path == SEARCH:
                self._handle_search(params)
            elif path == DOWNLOAD:
                self._handle_download(params)
            elif path == API_FILES:
                self._handle_api_files(params)
            elif path == HEALTH:
                self._handle_health()
            else:
                self._send_error(404, "Not found")

        except ValueError as e:
            self._send_error(400, str(e))
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            self._send_error(500, "Internal server error", str(e))

    def do_POST(self):
        try:
            if not self._check_rate_limit():
                return

            if not self._check_ip_filter():
                self._send_error(403, "Access denied")
                return

            if not self._validate_post_csrf():
                self._send_error(403, "CSRF validation failed. Please refresh the page and try again.")
                return

            parsed = urlparse(self.path)
            path = parsed.path

            if path == SAVE:
                self._handle_save()
            elif path == UPLOAD:
                self._handle_upload()
            elif path == MKDIR:
                self._handle_mkdir()
            elif path == DELETE:
                self._handle_delete_post()
            elif path == MOVE:
                self._handle_move()
            elif path == COPY:
                self._handle_copy()
            elif path == DOWNLOAD_SELECTED:
                self._handle_download_selected()
            else:
                self._send_error(404, "Not found")

        except ValueError as e:
            self._send_error(400, str(e))
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            self._send_error(500, "Internal server error", str(e))

    def _validate_post_csrf(self) -> bool:
        origin = self.headers.get('Origin')
        referer = self.headers.get('Referer')

        scheme = 'https' if self.config.security.ssl.enabled else 'http'
        host = self.headers.get('Host', f'{self.config.server.host}:{self.config.server.port}')
        expected_origin = f'{scheme}://{host}'

        if origin:
            if origin != expected_origin:
                return False
        elif referer:
            if not referer.startswith(expected_origin):
                return False

        content_type = self.headers.get('Content-Type', '')
        content_length = int(self.headers.get('Content-Length', 0))

        max_size = MAX_FORM_BODY_SIZE
        if content_type.startswith('multipart/form-data'):
            max_size = self.config.server.max_upload_size

        if content_length > 0 and content_length <= max_size:
            raw_body = self.rfile.read(content_length)
            self._buffered_body = raw_body

            if content_type.startswith('application/x-www-form-urlencoded'):
                try:
                    params = parse_qs(raw_body.decode('utf-8'))
                    form = {k: v[0] if v else '' for k, v in params.items()}
                    token = form.get('_csrf', '')
                    if token and not self._validate_csrf_token(token):
                        return False
                except Exception:
                    logger.warning("Error validating CSRF token", exc_info=True)

            elif content_type.startswith('multipart/form-data'):
                try:
                    token = self._extract_csrf_from_multipart(raw_body)
                    if token and not self._validate_csrf_token(token):
                        return False
                except Exception:
                    logger.warning("Error validating CSRF token in multipart", exc_info=True)

        return True

    def do_HEAD(self):
        self.do_GET()

    def _handle_root(self, params: Dict[str, str]):
        rel_path = params.get("p", "")
        sort_by = params.get("sort", self.config.ui.default_sort)
        show_hidden = params.get("hidden", "1" if self.config.ui.show_hidden else "0") == "1"
        try:
            page = int(params.get("page", "1"))
        except ValueError:
            page = 1

        if "edit" in params and rel_path and not rel_path.endswith("/"):
            self._handle_editor(params)
            return

        if "preview" in params and rel_path and not rel_path.endswith("/"):
            self._handle_preview(params)
            return

        target = self._resolve_path(rel_path)
        if target is None:
            return

        if not target.exists():
            self._send_error(404, f"Path not found: {escape_html(rel_path)}")
            return

        if target.is_file():
            self._handle_preview(params)
            return

        files = self.storage.list_directory(target, sort_by=sort_by, show_hidden=show_hidden)

        per_page = self.config.ui.items_per_page
        total_pages = max(1, (len(files) + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_files = files[start_idx:end_idx]

        flash_message = ""
        flash_type = "success"
        if "success" in params:
            flash_message = escape_html(params["success"])
            flash_type = "success"
        elif "error" in params:
            flash_message = escape_html(params["error"])
            flash_type = "error"

        html = render_listing(
            files=page_files,
            current_path=rel_path,
            sort_by=sort_by,
            show_hidden=show_hidden,
            flash_message=flash_message,
            flash_type=flash_type,
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
        if not self._check_feature('edit', 'Editing'):
            return
        rel_path = params.get("p", "")

        target = self._resolve_path(rel_path)
        if target is None:
            return

        if not target.exists():
            self._send_error(404, f"File not found: {escape_html(rel_path)}")
            return

        if not target.is_file():
            self._send_error(400, "Not a file")
            return

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error reading file: {e}")
            return

        html = render_editor(
            file_path=rel_path,
            content=content,
            csrf_token=self.csrf_token,
        )

        self._send_html(200, html, f"Edit: {escape_html(rel_path)}")

    def _handle_preview(self, params: Dict[str, str]):
        rel_path = params.get("p", "")

        target = self._resolve_path(rel_path)
        if target is None:
            return

        if not target.exists():
            self._send_error(404, f"File not found: {escape_html(rel_path)}")
            return

        if not target.is_file():
            self._send_error(400, "Not a file")
            return

        stat = target.stat()
        mime_type = guess_mime_type(target.name)
        is_text = self.storage.is_text_file(target)

        content = None
        if is_text:
            try:
                content = target.read_text(encoding="utf-8", errors="replace")
            except (OSError, PermissionError, UnicodeDecodeError):
                logger.warning(f"Could not read file content for preview: {rel_path}")

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
        rel_path = params.get("p", "")

        target = self._resolve_path(rel_path)
        if target is None:
            return

        if not target.exists():
            self._send_error(404, f"File not found: {escape_html(rel_path)}")
            return

        if not target.is_file():
            self._send_error(400, "Not a file")
            return

        stat = target.stat()
        mime_type = guess_mime_type(target.name) or "application/octet-stream"
        last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stat.st_mtime))

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

        extra_headers = {
            "Content-Disposition": get_content_disposition(target.name, mime_type),
            "Content-Length": str(stat.st_size),
            "Last-Modified": last_modified,
        }

        try:
            self._send_file_stream(target, mime_type, extra_headers)
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error reading file: {e}")

    def _handle_search(self, params: Dict[str, str]):
        query = params.get("q", "")
        rel_path = params.get("p", "")
        show_hidden = params.get("hidden", "1" if self.config.ui.show_hidden else "0") == "1"

        if not query:
            self._send_redirect(f"/?p={quote(rel_path)}")
            return

        search_path = self._resolve_path(rel_path)
        if search_path is None:
            return

        results = self.storage.search(query, search_path, show_hidden=show_hidden)

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
        if not self._check_feature('download_zip', 'Downloads'):
            return

        rel_path = params.get("p", "")

        target = self._resolve_path(rel_path)
        if target is None:
            return

        if not target.exists():
            self._send_error(404, f"Path not found: {escape_html(rel_path)}")
            return

        zip_path = self.storage.create_zip_file([target])
        if not zip_path:
            self._send_error(500, "Error creating ZIP")
            return

        filename = f"{target.name}.zip"
        extra_headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
        try:
            self._send_file_stream(zip_path, "application/zip", extra_headers)
        finally:
            zip_path.unlink(missing_ok=True)

    def _handle_api_files(self, params: Dict[str, str]):
        rel_path = params.get("p", "")
        sort_by = params.get("sort", "name")

        target = self._resolve_path(rel_path)
        if target is None:
            return

        if not target.is_dir():
            self._send_error(400, "Not a directory")
            return

        files = self.storage.list_directory(target, sort_by=sort_by)
        data = [f.to_dict() for f in files]

        self._send_response(
            200,
            json.dumps(data).encode("utf-8"),
            "application/json",
        )

    def _handle_health(self):
        data = {
            "status": "healthy",
            "version": __version__,
            "uptime": time.time() - self.start_time,
        }
        self._send_response(200, json.dumps(data).encode("utf-8"), "application/json")

    def _handle_save(self):
        if not self._check_feature('edit', 'Editing'):
            return

        form = self._get_form_data()
        rel_path = form.get("p", "")
        content = form.get("content", "")

        target = self._resolve_path(rel_path)
        if target is None:
            return

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            self._send_redirect(f"/?p={quote(rel_path)}&edit=1&saved=1")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error saving file: {e}")

    def _handle_upload(self):
        if not self._check_feature('upload', 'Uploads'):
            return

        fields, files = self._get_multipart_data()
        rel_path = fields.get("p", "")

        if not files:
            self._send_redirect(f"/?p={quote(rel_path)}&error=no_files")
            return

        target_dir = self._resolve_path(rel_path)
        if target_dir is None:
            return

        target_dir.mkdir(parents=True, exist_ok=True)

        saved = []
        for field_name, (filename, data) in files.items():
            safe_name = PathSecurity.sanitize_filename(filename)
            if not safe_name:
                continue

            if len(data) > self.config.server.max_upload_size:
                continue

            target_file = target_dir / safe_name
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

        if saved:
            msg = f"Uploaded: {', '.join(saved)}"
            self._send_redirect(f"/?p={quote(rel_path)}&success={quote(msg)}")
        else:
            self._send_redirect(f"/?p={quote(rel_path)}&error=upload_failed")

    def _handle_mkdir(self):
        if not self._check_feature('mkdir', 'Directory creation'):
            return

        form = self._get_form_data()
        rel_path = form.get("p", "")
        dir_name = form.get("name", "").strip()

        if not dir_name:
            self._send_error(400, "Directory name required")
            return

        if "/" in dir_name or "\\" in dir_name or ".." in dir_name:
            self._send_error(400, "Invalid directory name")
            return

        target = self._resolve_path(f"{rel_path}/{dir_name}" if rel_path else dir_name)
        if target is None:
            return

        try:
            target.mkdir(parents=True, exist_ok=True)
            self._send_redirect(f"/?p={quote(str(target.relative_to(self.config.get_root_path())))}")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error creating directory: {e}")

    def _handle_delete_post(self):
        if not self._check_feature('delete', 'Deletion'):
            return

        form = self._get_form_data()
        rel_path = form.get("p", "")

        target = self._resolve_path(rel_path)
        if target is None:
            return

        if not target.exists():
            self._send_error(404, "Path not found")
            return

        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

            logger.info(f"[{self.request_id}] Deleted: {rel_path}")

            parent = str(target.parent.relative_to(self.config.get_root_path()))
            self._send_redirect(f"/?p={quote(parent)}")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error deleting: {e}")

    def _handle_move(self):
        if not self._check_feature('move', 'Move'):
            return

        form = self._get_form_data()
        source = form.get("source", "")
        destination = form.get("destination", "")

        source_path = self._resolve_path(source)
        if source_path is None:
            return

        dest_path = self._resolve_path(destination)
        if dest_path is None:
            return

        if not source_path.exists():
            self._send_error(404, "Source not found")
            return

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_path))

            logger.info(f"[{self.request_id}] Moved: {source} -> {destination}")

            parent = str(dest_path.parent.relative_to(self.config.get_root_path()))
            self._send_redirect(f"/?p={quote(parent)}")
        except (OSError, PermissionError) as e:
            self._send_error(500, f"Error moving: {e}")

    def _handle_copy(self):
        if not self._check_feature('copy', 'Copy'):
            return

        form = self._get_form_data()
        source = form.get("source", "")
        destination = form.get("destination", "")

        source_path = self._resolve_path(source)
        if source_path is None:
            return

        dest_path = self._resolve_path(destination)
        if dest_path is None:
            return

        if not source_path.exists():
            self._send_error(404, "Source not found")
            return

        if not self.storage.copy(source_path, dest_path):
            self._send_error(500, "Error copying")
            return

        logger.info(f"[{self.request_id}] Copied: {source} -> {destination}")

        parent = str(dest_path.parent.relative_to(self.config.get_root_path()))
        self._send_redirect(f"/?p={quote(parent)}")

    def _handle_download_selected(self):
        if not self._check_feature('download_zip', 'Downloads'):
            return

        if not hasattr(self, '_buffered_body') or not self._buffered_body:
            self._send_error(400, "Request body not available")
            return

        body = self._buffered_body.decode('utf-8')
        params = parse_qs(body)

        current_path = params.get("p", [""])[0]
        selected_files = params.get("files", [])

        if not selected_files:
            self._send_error(400, "No files selected")
            return

        paths = []
        for file_path in selected_files:
            target = self._resolve_path(file_path)
            if target is not None and target.exists():
                paths.append(target)

        if not paths:
            self._send_error(404, "No valid files found")
            return

        zip_path = self.storage.create_zip_file(paths)
        if not zip_path:
            self._send_error(500, "Error creating ZIP")
            return

        if len(paths) == 1:
            filename = f"{paths[0].name}.zip"
        else:
            folder_name = current_path.split("/")[-1] if current_path else "files"
            filename = f"{folder_name}_selected.zip"

        extra_headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
        try:
            self._send_file_stream(zip_path, "application/zip", extra_headers)
        finally:
            zip_path.unlink(missing_ok=True)


def create_handler_class(config: Config):
    rate_limiter = RateLimiter(
        requests_per_minute=config.security.rate_limit.requests_per_minute,
        burst=config.security.rate_limit.burst,
    ) if config.security.rate_limit.enabled else None

    ip_filter = IPFilter(
        allowed_ips=config.security.allowed_ips,
        blocked_ips=config.security.blocked_ips,
    )

    security_headers = SecurityHeaders()

    csrf_secret_str = os.environ.get('FILESERVER_CSRF_SECRET')
    if csrf_secret_str:
        csrf_secret = bytes.fromhex(csrf_secret_str)
    else:
        csrf_secret = os.urandom(32)

    class ConfiguredHandler(FileServerHandler):
        _config = config
        _rate_limiter = rate_limiter
        _ip_filter = ip_filter
        _security_headers = security_headers
        _csrf_secret = csrf_secret
    return ConfiguredHandler
