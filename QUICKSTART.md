# Browser File Server — Quick Start

A modern, secure HTTP file server with web UI. Zero dependencies.

## Basic Usage

```bash
# Start with defaults (serves ~/ on port 8080)
python -m server

# Serve specific directory
python -m server /path/to/share

# Specify port
python -m server /path/to/share 9000
```

Then open: **http://localhost:8080**

## Background Mode

```bash
# Using the launch script
./start-fileserver.sh /path/to/share 8080

# Or manually
nohup python -m server /path/to/share 8080 > fileserver.log 2>&1 &
disown
```

## Useful Commands

```bash
# View logs
tail -f fileserver.log

# Stop server
pkill -f "python.*server"

# Check configuration
python -m server --check-config

# Show help
python -m server --help
```

## Features

- 📁 Browse directories
- 📝 Edit text files (Ctrl+S to save)
- 🔍 Search files
- ⬆️ Upload files (drag & drop)
- ⬇️ Download files/folders
- 🖼️ Preview images, videos, audio
- 🌓 Dark/Light theme

## Configuration

Create `config.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8080
  root: ~/files

ui:
  theme: dark
```

## Requirements

- Python 3.7+
- No external dependencies

## Legacy Usage

The original `fileserver.py` still works:

```bash
python3 fileserver.py ~/ 8080
```
