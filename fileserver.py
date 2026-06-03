#!/usr/bin/env python3
"""Tiny file server: browse, view, edit, upload, download files in the browser."""

import os, sys, html, urllib.parse, posixpath, mimetypes, shutil, io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~"))
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
HOST = "127.0.0.1"

TEXT_EXTS = {
    ".sh", ".bash", ".py", ".js", ".ts", ".mjs", ".cjs",
    ".html", ".htm", ".css", ".scss", ".less",
    ".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".conf", ".cfg",
    ".md", ".markdown", ".txt", ".log", ".csv", ".tsv",
    ".go", ".rs", ".java", ".c", ".h", ".cpp", ".hpp", ".cc", ".hh",
    ".rb", ".php", ".pl", ".lua", ".r", ".sql", ".diff", ".patch",
    ".env", ".gitignore", ".gitattributes", ".editorconfig",
    ".dockerfile", "Dockerfile", "Makefile", "CMakeLists.txt",
    ".zsh", ".fish", ".vim", ".awk", ".sed",
}

def is_text(path: str) -> bool:
    name = os.path.basename(path)
    base, ext = os.path.splitext(name)
    if ext.lower() in TEXT_EXTS:
        return True
    if name in ("Dockerfile", "Makefile", "CMakeLists.txt"):
        return True
    # Sniff: if first 8KB is mostly printable + common whitespace, treat as text
    try:
        with open(path, "rb") as f:
            sample = f.read(8192)
        if not sample:
            return True
        if b"\x00" in sample:
            return False
        printable = sum(1 for b in sample if 9 <= b <= 13 or 32 <= b <= 126 or b >= 128)
        return printable / len(sample) > 0.85
    except OSError:
        return False

def safe_join(root: str, rel: str) -> str:
    rel = rel.lstrip("/")
    target = os.path.normpath(os.path.join(root, rel))
    if os.path.commonpath([root, target]) != root:
        raise ValueError("path escapes root")
    return target

# ---- HTML ----

PAGE_HEAD = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{box-sizing:border-box}}
body{{font:14px -apple-system,system-ui,sans-serif;margin:0;background:#1e1e1e;color:#d4d4d4}}
a{{color:#7aa2f7;text-decoration:none}} a:hover{{text-decoration:underline}}
.bar{{background:#252526;padding:10px 12px;border-bottom:1px solid #3c3c3c;display:flex;flex-direction:column;gap:8px}}
.bar-row{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
.bar input[type=text]{{background:#3c3c3c;color:#d4d4d4;border:1px solid #555;padding:6px 10px;border-radius:3px;flex:1;min-width:100px;font-size:14px}}
.bar button{{background:#0e639c;color:#fff;border:0;padding:6px 14px;border-radius:3px;cursor:pointer;font-size:13px;white-space:nowrap}}
.bar button:hover{{background:#1177bb}}
.path{{font-family:monospace;color:#9cdcfe;word-break:break-all;font-size:13px}}
.btn{{display:inline-block;background:#0e639c;color:#fff;border:0;padding:5px 12px;border-radius:3px;cursor:pointer;font-size:13px;white-space:nowrap;text-align:center}}
.btn:hover{{background:#1177bb;text-decoration:none}}
.btn-del{{background:#a1260d}}
.btn-del:hover{{background:#c4350d}}
.btn-view{{background:#3a3d41}}
.btn-view:hover{{background:#4a4d51}}
textarea{{width:100%;min-height:70vh;background:#1e1e1e;color:#d4d4d4;border:1px solid #3c3c3c;font:13px Menlo,Consolas,monospace;padding:12px;border-radius:3px;tab-size:4;resize:vertical}}
.upzone{{padding:12px;background:#252526;border-radius:4px;margin:12px}}
input[type=file]{{color:#d4d4d4;flex:1;min-width:0}}
.flash{{background:#16825d;color:#fff;padding:8px 12px;border-radius:3px;margin:8px 12px}}
.warn{{background:#a1260d;color:#fff;padding:8px 12px;border-radius:3px;margin:8px 12px}}
.hint{{color:#888;font-size:12px;padding:0 12px 8px}}
.list{{list-style:none;padding:0;margin:0}}
.item{{display:flex;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid #2d2d2d;flex-wrap:wrap}}
.item:hover{{background:#2a2d2e}}
.item-main{{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}}
.item-name{{font-family:monospace;font-size:14px;word-break:break-all;display:flex;align-items:center;gap:6px}}
.item-name a{{color:#d4d4d4}}
.item-name a:hover{{color:#7aa2f7}}
.item-name.dir a{{color:#c586c0}}
.item-meta{{color:#888;font-size:11px;display:flex;gap:10px;flex-wrap:wrap}}
.item-actions{{display:flex;gap:6px;flex-shrink:0}}
.icon{{font-size:16px;line-height:1;flex-shrink:0}}
</style></head><body>"""

PAGE_FOOT = "</body></html>"

def listing(root: str, rel: str, flash: str = "") -> bytes:
    target = safe_join(root, rel)
    if not os.path.isdir(target):
        return error_page("Not a directory", rel)
    entries = sorted(os.listdir(target), key=lambda n: (not os.path.isdir(os.path.join(target, n)), n.lower()))
    items = []
    if rel:
        parent = posixpath.dirname(rel.rstrip("/")) or ""
        items.append(
            f'<li class=item>'
            f'<span class=icon>📁</span>'
            f'<div class=item-main><div class=item-name dir><a href="/?p={urllib.parse.quote(parent)}">..</a></div></div>'
            f'</li>'
        )
    for name in entries:
        full = os.path.join(target, name)
        is_dir = os.path.isdir(full)
        try:
            st = os.stat(full)
            size = "" if is_dir else format_size(st.st_size)
            mtime = format_time(st.st_mtime)
        except OSError:
            size = mtime = "?"
        sub = posixpath.join(rel, name) if rel else name
        quoted = urllib.parse.quote(sub)
        icon = "📁" if is_dir else icon_for(name)
        if is_dir:
            name_html = f'<a href="/?p={quoted}">{html.escape(name)}/</a>'
            primary = f'<a class=btn href="/?p={quoted}">open</a>'
        else:
            name_html = f'<a href="/raw?p={quoted}">{html.escape(name)}</a>'
            if is_text(full):
                primary = f'<a class=btn href="/?p={quoted}&edit=1">edit</a>'
            else:
                primary = f'<a class=btn href="/raw?p={quoted}">download</a>'
        del_btn = f'<a class="btn btn-del" href="/delete?p={quoted}" onclick="return confirm(\'Delete {html.escape(name)}?\')">del</a>'
        meta_bits = []
        if size:
            meta_bits.append(f'<span>{size}</span>')
        if mtime != "?":
            meta_bits.append(f'<span>{mtime}</span>')
        meta_html = '<div class=item-meta>' + ''.join(meta_bits) + '</div>' if meta_bits else ''
        name_class = "item-name dir" if is_dir else "item-name"
        items.append(
            f'<li class=item>'
            f'<span class=icon>{icon}</span>'
            f'<div class=item-main>'
            f'<div class={name_class}>{name_html}</div>'
            f'{meta_html}'
            f'</div>'
            f'<div class=item-actions>{primary}{del_btn}</div>'
            f'</li>'
        )

    flash_html = f'<div class=flash>{html.escape(flash)}</div>' if flash else ""
    body = f"""
<div class=bar>
  <div class=bar-row>
    <a class=btn href="/?p={urllib.parse.quote(posixpath.dirname(rel.rstrip("/")) or "")}">↑ up</a>
    <span class=path>/{html.escape(rel)}</span>
  </div>
  <form class=bar-row method=post action="/mkdir">
    <input type=hidden name=p value="{html.escape(rel)}">
    <input type=text name=name placeholder="new folder name" required>
    <button>+folder</button>
  </form>
  <form class=bar-row method=post action="/upload" enctype=multipart/form-data>
    <input type=hidden name=p value="{html.escape(rel)}">
    <input type=file name=f multiple>
    <button>upload</button>
  </form>
</div>
{flash_html}
<div class=hint>Tap a name to view. Use the buttons to edit / download / delete. Folders use "open".</div>
<ul class=list>
  {''.join(items)}
</ul>
"""
    page = PAGE_HEAD.format(title=f"/{rel}") + body + PAGE_FOOT
    return page.encode("utf-8")

def editor(root: str, rel: str, content: str, flash: str = "") -> bytes:
    quoted = urllib.parse.quote(rel)
    flash_html = f'<div class=flash>{html.escape(flash)}</div>' if flash else ""
    body = f"""
<div class=bar>
  <a class=btn href="/?p={urllib.parse.quote(posixpath.dirname(rel) or '')}">← back</a>
  <span class=path>/{html.escape(rel)}</span>
  <a class=btn style="background:#16825d" href="/?p={quoted}">view</a>
</div>
{flash_html}
<form method=post action="/save" style="padding:12px">
  <input type=hidden name=p value="{html.escape(rel)}">
  <textarea name=content spellcheck=false>{html.escape(content)}</textarea>
  <div style="margin-top:8px;display:flex;gap:8px;align-items:center">
    <button type=submit>💾 Save</button>
    <span class=hint>Ctrl+S to save</span>
  </div>
</form>
<script>
document.addEventListener('keydown',e=>{{
  if((e.ctrlKey||e.metaKey)&&e.key==='s'){{e.preventDefault();document.querySelector('form').submit()}}
}});
</script>
"""
    return (PAGE_HEAD.format(title=rel) + body + PAGE_FOOT).encode("utf-8")

def error_page(msg: str, rel: str = "") -> bytes:
    body = f'<div class=bar><a class=btn href="/?p=">home</a></div><div class=warn>{html.escape(msg)}</div>'
    return (PAGE_HEAD.format(title="error") + body + PAGE_FOOT).encode("utf-8")

def icon_for(name: str) -> str:
    ext = os.path.splitext(name)[1].lower()
    return {".sh": "⚙️", ".py": "🐍", ".md": "📝", ".json": "📋", ".txt": "📄",
            ".png": "🖼️", ".jpg": "🖼️", ".jpeg": "🖼️", ".gif": "🖼️", ".webp": "🖼️",
            ".mp4": "🎬", ".mkv": "🎬", ".mov": "🎬", ".webm": "🎬",
            ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵", ".ogg": "🎵",
            ".pdf": "📕", ".zip": "🗜️", ".tar": "🗜️", ".gz": "🗜️",
            ".go": "🦫", ".rs": "🦀", ".js": "📜", ".ts": "📜", ".html": "🌐",
            ".css": "🎨"}.get(ext, "📄")

def format_size(n: int) -> str:
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.0f}{u}" if u == "B" else f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def format_time(t: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")

# ---- Handler ----

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.address_string()} {fmt%args}\n")

    def _send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8", extra_headers: dict | None = None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            rel = qs.get("p", [""])[0]

            if parsed.path == "/" or parsed.path == "":
                if "edit" in qs and rel and not rel.endswith("/"):
                    target = safe_join(ROOT, rel)
                    if not os.path.isfile(target):
                        return self._send(404, error_page("File not found", rel))
                    with open(target, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    return self._send(200, editor(ROOT, rel, content))
                return self._send(200, listing(ROOT, rel))

            if parsed.path == "/raw":
                target = safe_join(ROOT, rel)
                if not os.path.isfile(target):
                    return self._send(404, b"Not found", "text/plain")
                ctype, _ = mimetypes.guess_type(target)
                ctype = ctype or "application/octet-stream"
                # Inline for text/*, attachment otherwise
                disp = "inline" if (ctype.startswith("text/") or ctype in ("application/json", "application/xml")) else "attachment"
                fname = os.path.basename(target)
                with open(target, "rb") as f:
                    data = f.read()
                return self._send(200, data, ctype, {"Content-Disposition": f'{disp}; filename="{fname}"'})

            if parsed.path == "/delete":
                target = safe_join(ROOT, rel)
                if not os.path.exists(target):
                    return self._send(404, error_page("Not found", rel))
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
                parent = posixpath.dirname(rel) or ""
                self.send_response(303)
                self.send_header("Location", f"/?p={urllib.parse.quote(parent)}")
                self.end_headers()
                return

            return self._send(404, error_page("Unknown path"))
        except ValueError as e:
            return self._send(400, error_page(f"Bad path: {e}"))
        except Exception as e:
            return self._send(500, error_page(f"Server error: {e}"))

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            qs = urllib.parse.parse_qs(parsed.query)

            if parsed.path == "/save":
                # application/x-www-form-urlencoded
                form = urllib.parse.parse_qs(body.decode("utf-8"))
                rel = form.get("p", [""])[0]
                content = form.get("content", [""])[0]
                target = safe_join(ROOT, rel)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
                return self._send(200, editor(ROOT, rel, content, f"✓ saved {rel}"))

            if parsed.path == "/mkdir":
                form = urllib.parse.parse_qs(body.decode("utf-8"))
                rel = form.get("p", [""])[0]
                name = form.get("name", [""])[0].strip()
                if not name or "/" in name or ".." in name:
                    return self._send(400, error_page("Bad folder name"))
                target = safe_join(ROOT, posixpath.join(rel, name))
                os.makedirs(target, exist_ok=True)
                self.send_response(303)
                self.send_header("Location", f"/?p={urllib.parse.quote(posixpath.join(rel, name))}")
                self.end_headers()
                return

            if parsed.path == "/upload":
                # multipart/form-data
                ctype = self.headers.get("Content-Type", "")
                if not ctype.startswith("multipart/form-data"):
                    return self._send(400, error_page("Expected multipart"))
                boundary = ctype.split("boundary=", 1)[1].strip().strip('"').encode()
                target_dir_rel = ""
                saved = []
                for part in body.split(b"--" + boundary):
                    part = part.strip(b"\r\n")
                    if not part or part == b"--":
                        continue
                    hdr, _, data = part.partition(b"\r\n\r\n")
                    data = data.rstrip(b"\r\n")
                    hdr_lines = hdr.split(b"\r\n")
                    disp = next((h for h in hdr_lines if h.lower().startswith(b"content-disposition")), b"")
                    name_match = b'name="' in disp
                    if not name_match:
                        continue
                    # Extract field name
                    fname_marker = b'filename="'
                    if fname_marker not in disp:
                        # form field, e.g. 'p'
                        field_name = disp.split(b'name="', 1)[1].split(b'"', 1)[0]
                        if field_name == b"p":
                            target_dir_rel = data.decode("utf-8", "replace")
                        continue
                    # File field
                    field_name = disp.split(b'name="', 1)[1].split(b'"', 1)[0]
                    if field_name != b"f":
                        continue
                    fname = disp.split(b'filename="', 1)[1].split(b'"', 1)[0].decode("utf-8", "replace")
                    if not fname:
                        continue
                    fname = os.path.basename(fname)
                    dest_dir = safe_join(ROOT, target_dir_rel)
                    os.makedirs(dest_dir, exist_ok=True)
                    dest = os.path.join(dest_dir, fname)
                    with open(dest, "wb") as f:
                        f.write(data)
                    saved.append(fname)
                flash = f"✓ uploaded: {', '.join(saved)}" if saved else "no files"
                self.send_response(303)
                self.send_header("Location", f"/?p={urllib.parse.quote(target_dir_rel)}&flash={urllib.parse.quote(flash)}")
                self.end_headers()
                return

            return self._send(404, error_page("Unknown POST endpoint"))
        except ValueError as e:
            return self._send(400, error_page(f"Bad path: {e}"))
        except Exception as e:
            return self._send(500, error_page(f"Server error: {e}"))


def main():
    os.chdir(ROOT)
    print(f"[fileserver] serving {ROOT} on http://{HOST}:{PORT}", flush=True)
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    srv.serve_forever()

if __name__ == "__main__":
    main()
