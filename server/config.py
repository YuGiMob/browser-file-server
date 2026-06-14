"""
Configuration management for the file server.

Supports configuration via:
1. Configuration file (YAML)
2. Environment variables
3. Command-line arguments

Priority: CLI args > Environment variables > Config file > Defaults
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


# Default configuration values
DEFAULTS = {
    "server": {
        "host": "127.0.0.1",
        "port": 8080,
        "root": "~",
        "max_upload_size": 100 * 1024 * 1024,  # 100MB
        "workers": 1,
        "timeout": 30,
    },
    "security": {
        "ssl": {
            "enabled": False,
            "certfile": "",
            "keyfile": "",
        },
        "rate_limit": {
            "enabled": True,
            "requests_per_minute": 60,
            "burst": 10,
        },
        "allowed_ips": [],
        "blocked_ips": [],
        "cors": {
            "enabled": False,
            "origins": ["*"],
        },
    },
    "features": {
        "search": True,
        "preview": True,
        "upload": True,
        "delete": True,
        "mkdir": True,
        "edit": True,
        "download_zip": True,
        "move": True,
        "copy": True,
    },
    "ui": {
        "theme": "dark",  # dark, light, auto
        "items_per_page": 100,
        "show_hidden": False,
        "default_sort": "name",  # name, size, modified
        "show_preview": True,
        "show_thumbnails": True,
    },
    "logging": {
        "level": "INFO",
        "file": "",
        "max_size": 10 * 1024 * 1024,  # 10MB
        "backup_count": 5,
        "format": "text",  # text, json
    },
}


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "127.0.0.1"
    port: int = 8080
    root: str = "~"
    max_upload_size: int = 100 * 1024 * 1024
    workers: int = 1
    timeout: int = 30


@dataclass
class SSLConfig:
    """SSL configuration."""
    enabled: bool = False
    certfile: str = ""
    keyfile: str = ""


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    requests_per_minute: int = 60
    burst: int = 10


@dataclass
class SecurityConfig:
    """Security configuration."""
    ssl: SSLConfig = field(default_factory=SSLConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    allowed_ips: List[str] = field(default_factory=list)
    blocked_ips: List[str] = field(default_factory=list)
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_enabled: bool = False


@dataclass
class FeaturesConfig:
    """Feature flags configuration."""
    search: bool = True
    preview: bool = True
    upload: bool = True
    delete: bool = True
    mkdir: bool = True
    edit: bool = True
    download_zip: bool = True
    move: bool = True
    copy: bool = True


@dataclass
class UIConfig:
    """UI configuration."""
    theme: str = "dark"
    items_per_page: int = 100
    show_hidden: bool = False
    default_sort: str = "name"
    show_preview: bool = True
    show_thumbnails: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: str = ""
    max_size: int = 10 * 1024 * 1024
    backup_count: int = 5
    format: str = "text"


@dataclass
class Config:
    """Main configuration."""
    server: ServerConfig = field(default_factory=ServerConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def get_root_path(self) -> Path:
        """Get the resolved root path."""
        return Path(self.server.root).expanduser().resolve()


def load_config_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        # Try default locations
        candidates = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "config.yml",
            Path.home() / ".fileserver" / "config.yaml",
            Path("/etc/fileserver/config.yaml"),
        ]
        for candidate in candidates:
            if candidate.exists():
                config_path = str(candidate)
                break

    if config_path is None or not Path(config_path).exists():
        return {}

    try:
        # Try to import yaml (optional dependency)
        import yaml
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: simple key=value parsing
        return _parse_simple_config(config_path)


def _parse_simple_config(config_path: str) -> Dict[str, Any]:
    """Parse simple key=value configuration file."""
    config = {}
    current_section = config

    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.endswith(":"):
                # Section header
                section_name = line[:-1].strip()
                if section_name not in config:
                    config[section_name] = {}
                current_section = config[section_name]
            elif "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Parse value
                if value.lower() in ("true", "yes", "1"):
                    value = True
                elif value.lower() in ("false", "no", "0"):
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif "," in value:
                    value = [v.strip() for v in value.split(",")]

                current_section[key] = value

    return config


def merge_configs(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two configuration dictionaries."""
    result = defaults.copy()

    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def apply_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration."""
    env_mappings = {
        "FILESERVER_HOST": ("server", "host"),
        "FILESERVER_PORT": ("server", "port"),
        "FILESERVER_ROOT": ("server", "root"),
        "FILESERVER_MAX_UPLOAD": ("server", "max_upload_size"),
        "FILESERVER_SSL_ENABLED": ("security", "ssl", "enabled"),
        "FILESERVER_SSL_CERT": ("security", "ssl", "certfile"),
        "FILESERVER_SSL_KEY": ("security", "ssl", "keyfile"),
        "FILESERVER_LOG_LEVEL": ("logging", "level"),
        "FILESERVER_LOG_FILE": ("logging", "file"),
        "FILESERVER_THEME": ("ui", "theme"),
    }

    for env_var, path in env_mappings.items():
        value = os.environ.get(env_var)
        if value is not None:
            # Navigate to the correct nested dict
            d = config
            for key in path[:-1]:
                if key not in d:
                    d[key] = {}
                d = d[key]

            # Parse and set value
            final_key = path[-1]
            if final_key in ("enabled",):
                d[final_key] = value.lower() in ("true", "yes", "1")
            elif final_key in ("port", "max_upload_size"):
                try:
                    d[final_key] = int(value)
                except ValueError:
                    pass
            else:
                d[final_key] = value

    return config


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="fileserver",
        description="Browser File Server - A modern, secure file server with web UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Start with defaults (~/ on port 8080)
  %(prog)s /path/to/share 9000      # Serve specific directory on port 9000
  %(prog)s --ssl cert.pem key.pem    # Enable HTTPS
  %(prog)s --config /etc/fs.yaml     # Use configuration file
  
Environment Variables:
  FILESERVER_HOST        Server host (default: 127.0.0.1)
  FILESERVER_PORT        Server port (default: 8080)
  FILESERVER_ROOT        Root directory to serve
  FILESERVER_SSL_*       SSL settings
  FILESERVER_LOG_*       Logging settings
        """,
    )

    parser.add_argument(
        "root",
        nargs="?",
        default=None,
        help="Root directory to serve (default: ~)",
    )
    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=None,
        help="Port to listen on (default: 8080)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--ssl",
        nargs=2,
        default=None,
        metavar=("CERT", "KEY"),
        help="Enable HTTPS with certificate and key files",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Log to file instead of stderr",
    )
    parser.add_argument(
        "--theme",
        default=None,
        choices=["dark", "light", "auto"],
        help="UI theme",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Disable file upload",
    )
    parser.add_argument(
        "--no-delete",
        action="store_true",
        help="Disable file deletion",
    )
    parser.add_argument(
        "--show-hidden",
        action="store_true",
        help="Show hidden files (starting with .)",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate configuration and exit",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {__import__('server').__version__}",
    )

    return parser.parse_args()


def build_config() -> Config:
    """Build configuration from all sources."""
    # Start with defaults
    config_dict = DEFAULTS.copy()

    # Load config file
    args = parse_args()
    file_config = load_config_file(args.config)
    config_dict = merge_configs(config_dict, file_config)

    # Apply environment variables
    config_dict = apply_env_vars(config_dict)

    # Apply CLI arguments
    if args.root is not None:
        config_dict["server"]["root"] = args.root
    if args.port is not None:
        config_dict["server"]["port"] = args.port
    if args.host is not None:
        config_dict["server"]["host"] = args.host
    if args.ssl is not None:
        config_dict["security"]["ssl"]["enabled"] = True
        config_dict["security"]["ssl"]["certfile"] = args.ssl[0]
        config_dict["security"]["ssl"]["keyfile"] = args.ssl[1]
    if args.log_level is not None:
        config_dict["logging"]["level"] = args.log_level
    if args.log_file is not None:
        config_dict["logging"]["file"] = args.log_file
    if args.theme is not None:
        config_dict["ui"]["theme"] = args.theme
    if args.no_upload:
        config_dict["features"]["upload"] = False
    if args.no_delete:
        config_dict["features"]["delete"] = False
    if args.show_hidden:
        config_dict["ui"]["show_hidden"] = True

    # Build Config object
    config = Config(
        server=ServerConfig(
            host=config_dict["server"]["host"],
            port=config_dict["server"]["port"],
            root=config_dict["server"]["root"],
            max_upload_size=config_dict["server"]["max_upload_size"],
            workers=config_dict["server"]["workers"],
            timeout=config_dict["server"]["timeout"],
        ),
        security=SecurityConfig(
            ssl=SSLConfig(
                enabled=config_dict["security"]["ssl"]["enabled"],
                certfile=config_dict["security"]["ssl"]["certfile"],
                keyfile=config_dict["security"]["ssl"]["keyfile"],
            ),
            rate_limit=RateLimitConfig(
                enabled=config_dict["security"]["rate_limit"]["enabled"],
                requests_per_minute=config_dict["security"]["rate_limit"]["requests_per_minute"],
                burst=config_dict["security"]["rate_limit"]["burst"],
            ),
            allowed_ips=config_dict["security"]["allowed_ips"],
            blocked_ips=config_dict["security"]["blocked_ips"],
            cors_enabled=config_dict["security"]["cors"]["enabled"],
            cors_origins=config_dict["security"]["cors"]["origins"],
        ),
        features=FeaturesConfig(**config_dict["features"]),
        ui=UIConfig(**config_dict["ui"]),
        logging=LoggingConfig(**config_dict["logging"]),
    )

    # Validate configuration
    if args.check_config:
        validate_config(config)
        print("Configuration is valid!")
        sys.exit(0)

    return config


def validate_config(config: Config) -> None:
    """Validate configuration and raise errors for invalid settings."""
    root = config.get_root_path()
    if not root.exists():
        raise ValueError(f"Root directory does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Root path is not a directory: {root}")

    if config.security.ssl.enabled:
        cert = Path(config.security.ssl.certfile)
        key = Path(config.security.ssl.keyfile)
        if not cert.exists():
            raise ValueError(f"SSL certificate not found: {cert}")
        if not key.exists():
            raise ValueError(f"SSL key not found: {key}")

    if config.server.port < 1 or config.server.port > 65535:
        raise ValueError(f"Invalid port number: {config.server.port}")

    if config.server.max_upload_size < 0:
        raise ValueError(f"Invalid max upload size: {config.server.max_upload_size}")
