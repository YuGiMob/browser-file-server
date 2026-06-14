# Browser File Server

A modern, secure HTTP file server with a beautiful web UI. Written in Python with zero external dependencies.

## Features

### Core Features
- 📁 **Directory Browsing** - Navigate folders with beautiful UI
- 📝 **File Editing** - Edit text files in-browser with Ctrl+S to save
- 🔍 **Search** - Find files quickly with full-text search
- ⬆️ **Upload** - Drag-and-drop file uploads
- ⬇️ **Download** - Download files and folders (as ZIP)
- 📁 **Create Folders** - Create new directories
- 🗑️ **Delete** - Remove files and folders
- ✏️ **Move/Rename** - Move or rename files
- 📋 **Copy** - Copy files and directories

### Security
- 🔒 **HTTPS/SSL** - SSL/TLS support
- 🛡️ **Path Traversal Protection** - Prevents directory escape attacks
- ⏱️ **Rate Limiting** - Prevents abuse
- 🚫 **IP Filtering** - Allow/block specific IPs
- 🔑 **CSRF Protection** - Prevents cross-site request forgery
- 🛡️ **Security Headers** - CSP, HSTS, X-Frame-Options, etc.

### Preview
- 🖼️ **Images** - View images directly in browser
- 🎬 **Videos** - Built-in video player
- 🎵 **Audio** - Built-in audio player
- 📄 **Documents** - Preview text files with syntax highlighting
- 📑 **Markdown** - Side-by-side markdown preview
- 📕 **PDF** - Embedded PDF viewer

### User Interface
- 🌓 **Dark/Light Theme** - Toggle between themes
- 📱 **Responsive** - Works on mobile devices
- ⌨️ **Keyboard Shortcuts** - Efficient navigation
- 🔔 **Toast Notifications** - User feedback
- 📊 **File Info** - Size, date, permissions
- 🏷️ **File Icons** - Visual file type indicators

### Configuration
- 📄 **Config File** - YAML configuration support
- 🔧 **CLI Arguments** - Command-line options
- 🌍 **Environment Variables** - Env var overrides
- 📝 **Logging** - Configurable logging with rotation

## Quick Start

### Basic Usage

```bash
# Start with defaults (serves ~/ on port 8080)
python -m server

# Serve specific directory
python -m server /path/to/share

# Specify port
python -m server /path/to/share 9000
```

### With HTTPS

```bash
# Start with SSL
python -m server --ssl cert.pem key.pem
```

### Using Configuration File

```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit config
nano config.yaml

# Start with config
python -m server --config config.yaml
```

### Background Mode

```bash
# Using the launch script
./start.sh /path/to/share 8080

# Or manually
nohup python -m server /path/to/share 8080 > fileserver.log 2>&1 &
```

## Installation

### Requirements

- Python 3.7 or higher
- No external dependencies (uses only stdlib)

### Optional Dependencies

```bash
# For YAML config support
pip install pyyaml
```

## Configuration

### Configuration File

Create `config.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8080
  root: ~/files

security:
  ssl:
    enabled: false

features:
  upload: true
  delete: true
  edit: true

ui:
  theme: dark
  show_hidden: false
```

### Environment Variables

```bash
export FILESERVER_HOST=0.0.0.0
export FILESERVER_PORT=8080
export FILESERVER_ROOT=/path/to/share
```

### Command-Line Arguments

```bash
python -m server [OPTIONS] [ROOT] [PORT]

Options:
  --host HOST           Host to bind to
  --port PORT           Port to listen on
  --config FILE         Path to config file
  --ssl CERT KEY        Enable HTTPS
  --log-level LEVEL     Set log level
  --log-file FILE       Log to file
  --theme THEME         UI theme (dark/light/auto)
  --no-upload           Disable uploads
  --no-delete           Disable deletion
  --show-hidden         Show hidden files
  --check-config        Validate configuration
  --version             Show version
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save file (in editor) |
| `/` | Focus search |
| `Escape` | Blur input / Go back |
| `E` | Edit file (in preview) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Directory listing or file preview |
| GET | `/?p=PATH` | View specific path |
| GET | `/?p=PATH&edit=1` | Edit file |
| GET | `/raw?p=PATH` | Download file |
| GET | `/search?q=QUERY` | Search files |
| GET | `/download?p=PATH` | Download folder as ZIP |
| GET | `/api/files` | JSON file listing |
| GET | `/health` | Health check |
| POST | `/save` | Save file |
| POST | `/upload` | Upload files |
| POST | `/mkdir` | Create directory |
| POST | `/delete` | Delete file/folder |
| POST | `/move` | Move/rename file |
| POST | `/copy` | Copy file |

## Development

### Project Structure

```
fileserver/
├── server/
│   ├── __init__.py      # Package init
│   ├── __main__.py      # Entry point
│   ├── config.py        # Configuration
│   ├── handler.py       # HTTP handler
│   ├── security.py      # Security utilities
│   ├── storage.py       # File operations
│   ├── templates/       # HTML templates
│   └── utils/           # Utility functions
├── fileserver.py        # Legacy entry point
├── config.example.yaml  # Example config
├── start.sh             # Launch script
├── tests/               # Unit tests
└── README.md            # This file
```

### Running Tests

```bash
# Run all tests
python -m unittest discover tests/

# Run specific test
python -m unittest tests.test_security
```

## License

MIT License
