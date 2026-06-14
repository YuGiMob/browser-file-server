"""
Main entry point for the file server.

Usage:
    python -m server [options]
    python -m server /path/to/share 9000
    python -m server --ssl cert.pem key.pem
"""

import os
import sys
import signal
import logging
from http.server import ThreadingHTTPServer
from typing import Optional

from . import __version__
from .config import build_config, validate_config, Config
from .handler import create_handler_class


def setup_logging(config: Config):
    """Set up logging configuration."""
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if config.logging.format == "json":
        log_format = '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    # File handler (if configured)
    if config.logging.file:
        try:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                config.logging.file,
                maxBytes=config.logging.max_size,
                backupCount=config.logging.backup_count,
            )
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        except Exception as e:
            logging.warning(f"Could not set up file logging: {e}")

    logging.basicConfig(
        level=log_level,
        handlers=handlers,
    )


def create_server(config: Config) -> ThreadingHTTPServer:
    """Create HTTP server with configuration."""
    handler_class = create_handler_class(config)

    # Create server
    server = ThreadingHTTPServer(
        (config.server.host, config.server.port),
        handler_class,
    )

    # Set timeout
    server.timeout = config.server.timeout

    return server


def run_server(config: Config):
    """Run the file server."""
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)

    # Validate configuration
    try:
        validate_config(config)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Create server
    server = create_server(config)

    # Setup SSL if configured
    if config.security.ssl.enabled:
        import ssl
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            config.security.ssl.certfile,
            config.security.ssl.keyfile,
        )
        server.socket = context.wrap_socket(
            server.socket,
            server_side=True,
        )

    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info("Shutting down...")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Print startup info
    root = config.get_root_path()
    host = config.server.host
    port = config.server.port
    ssl_info = " (HTTPS)" if config.security.ssl.enabled else ""

    print(f"\n{'='*60}")
    print(f"  Browser File Server v{__version__}")
    print(f"{'='*60}")
    print(f"  Serving: {root}")
    print(f"  Address: http://{host}:{port}{ssl_info}")
    print(f"{'='*60}")
    print(f"\n  Press Ctrl+C to stop\n")

    # Start server
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    """Main entry point."""
    try:
        # Build configuration
        config = build_config()

        # Run server
        run_server(config)

    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
