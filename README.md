# browser-file-server

A tiny, dependency-free HTTP file server written in ~250 lines of Python stdlib.

Designed for environments where you can't install extra packages (e.g. UserLAnd on
Android) and other file-server tools refuse to start because of missing Linux
capabilities.

## Features

- Browse directories
- View any text file inline (auto-detected by extension + content sniffing)
- Edit text files in-browser with Ctrl+S to save
- Upload files (multi-file)
- Create new folders
- Delete files and folders
- Path-traversal protection (can't escape the served root)
- No login, no database, no external dependencies

## Usage

```bash
python3 fileserver.py [ROOT] [PORT]
# defaults: ROOT = $HOME,  PORT = 8080
```

Then open `http://localhost:8080` in a browser.

To run it in the background on a phone (e.g. inside UserLAnd):

```bash
nohup python3 fileserver.py ~/ 8080 > fileserver.log 2>&1 &
disown
```

Or use the included `start-fileserver.sh` script.

## Background

`dufs` and `miniserve` both failed to start in a UserLAnd container because
they require capabilities (`CAP_NET_ADMIN`) the container doesn't grant. This
server uses only `http.server` and `socketserver` from the standard library
and works everywhere Python 3 does.

## License

MIT
