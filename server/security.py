"""
Security utilities for the file server.

Provides:
- Path traversal protection
- Rate limiting
- IP filtering
- Security headers
"""

import os
import time
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote
import ipaddress


class PathSecurity:
    """Path traversal protection and validation."""

    # Characters that are dangerous in filenames
    DANGEROUS_CHARS = set('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
                          '\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f')

    # Reserved names on Windows
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
    }

    @staticmethod
    def safe_join(root: Path, rel_path: str) -> Path:
        """
        Safely join root and relative path, preventing path traversal.

        Args:
            root: Root directory
            rel_path: Relative path to join

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path escapes root or contains dangerous characters
        """
        # Normalize the relative path
        rel_path = rel_path.lstrip("/")

        # Decode URL encoding
        rel_path = unquote(rel_path)

        # Check for null bytes
        if '\x00' in rel_path:
            raise ValueError("Path contains null byte")

        # Check for path traversal attempts
        parts = rel_path.split('/')
        for part in parts:
            if part == '..':
                raise ValueError("Path traversal attempt detected")
            if part == '.':
                continue
            if not part:
                continue

            # Check for dangerous characters
            if any(c in PathSecurity.DANGEROUS_CHARS for c in part):
                raise ValueError("Path contains dangerous characters")

            # Check for reserved names (Windows)
            name = part.split('.')[0].upper()
            if name in PathSecurity.RESERVED_NAMES:
                raise ValueError(f"Path contains reserved name: {part}")

        # Build the target path
        target = root / rel_path

        # Resolve to absolute path
        try:
            target = target.resolve()
        except (OSError, ValueError) as e:
            raise ValueError(f"Invalid path: {e}")

        # Ensure target is under root
        try:
            target.relative_to(root.resolve())
        except ValueError:
            raise ValueError("Path escapes root directory")

        return target

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename for safe storage.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove directory separators
        filename = filename.replace('/', '_').replace('\\', '_')

        # Remove null bytes
        filename = filename.replace('\x00', '')

        # Remove path traversal sequences
        filename = filename.replace('..', '')

        # Remove other dangerous characters
        for c in PathSecurity.DANGEROUS_CHARS:
            filename = filename.replace(c, '')

        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255 - len(ext)] + ext

        # Ensure filename is not empty
        if not filename or filename == '.':
            filename = 'unnamed'

        return filename

    @staticmethod
    def is_safe_path(path: str) -> bool:
        """Check if a path string is safe."""
        try:
            PathSecurity.safe_join(Path('/'), path)
            return True
        except ValueError:
            return False


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            burst: Maximum burst size
        """
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.tokens_per_second = requests_per_minute / 60.0
        self.buckets: Dict[str, Tuple[float, float]] = {}  # ip -> (tokens, last_update)

    def is_allowed(self, client_ip: str) -> Tuple[bool, Optional[int]]:
        """
        Check if a request from the given IP is allowed.

        Args:
            client_ip: Client IP address

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()

        if client_ip not in self.buckets:
            self.buckets[client_ip] = (float(self.burst), now)

        tokens, last_update = self.buckets[client_ip]

        # Add tokens based on time elapsed
        elapsed = now - last_update
        tokens = min(self.burst, tokens + elapsed * self.tokens_per_second)

        if tokens >= 1:
            tokens -= 1
            self.buckets[client_ip] = (tokens, now)
            return True, None
        else:
            # Calculate retry after
            retry_after = int((1 - tokens) / self.tokens_per_second) + 1
            self.buckets[client_ip] = (tokens, now)
            return False, retry_after

    def cleanup(self, max_age: float = 300) -> None:
        """Remove old entries."""
        now = time.time()
        to_remove = []
        for ip, (_, last_update) in self.buckets.items():
            if now - last_update > max_age:
                to_remove.append(ip)
        for ip in to_remove:
            del self.buckets[ip]


class IPFilter:
    """IP-based access control."""

    def __init__(
        self,
        allowed_ips: Optional[List[str]] = None,
        blocked_ips: Optional[List[str]] = None,
    ):
        """
        Initialize IP filter.

        Args:
            allowed_ips: List of allowed IP addresses/networks (empty = all allowed)
            blocked_ips: List of blocked IP addresses/networks
        """
        self.allowed_networks = self._parse_networks(allowed_ips or [])
        self.blocked_networks = self._parse_networks(blocked_ips or [])

    @staticmethod
    def _parse_networks(ip_list: List[str]) -> List[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        """Parse IP addresses and networks."""
        networks = []
        for ip_str in ip_list:
            try:
                # Try as network
                networks.append(ipaddress.ip_network(ip_str, strict=False))
            except ValueError:
                try:
                    # Try as single address
                    networks.append(ipaddress.ip_address(ip_str))
                except ValueError:
                    pass  # Skip invalid entries
        return networks

    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if a client IP is allowed.

        Args:
            client_ip: Client IP address

        Returns:
            True if allowed
        """
        try:
            ip = ipaddress.ip_address(client_ip)
        except ValueError:
            return False

        # Check blocked list first
        for network in self.blocked_networks:
            if isinstance(network, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
                if ip in network:
                    return False
            elif ip == network:
                return False

        # If allowed list is empty, allow all (except blocked)
        if not self.allowed_networks:
            return True

        # Check allowed list
        for network in self.allowed_networks:
            if isinstance(network, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
                if ip in network:
                    return True
            elif ip == network:
                return True

        return False


class SecurityHeaders:
    """Security header management."""

    @staticmethod
    def get_headers(
        csp_enabled: bool = True,
        hsts_enabled: bool = False,
    ) -> Dict[str, str]:
        """
        Get security headers.

        Args:
            csp_enabled: Whether to include Content Security Policy
            hsts_enabled: Whether to include HSTS header

        Returns:
            Dictionary of headers
        """
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }

        if csp_enabled:
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )

        if hsts_enabled:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return headers


class CSRFProtection:
    """CSRF token generation and validation."""

    def __init__(self, secret: str):
        """
        Initialize CSRF protection.

        Args:
            secret: Secret key for token generation
        """
        self.secret = secret.encode() if isinstance(secret, str) else secret

    def generate_token(self) -> str:
        """Generate a CSRF token."""
        import hmac
        import hashlib

        token = secrets.token_hex(32)
        timestamp = str(int(time.time()))
        signature = hmac.new(
            self.secret,
            f"{token}{timestamp}".encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{token}.{timestamp}.{signature}"

    def validate_token(self, token: str, max_age: int = 3600) -> bool:
        """
        Validate a CSRF token.

        Args:
            token: Token to validate
            max_age: Maximum token age in seconds

        Returns:
            True if token is valid
        """
        import hmac
        import hashlib

        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False

            token_part, timestamp_str, signature = parts

            # Check timestamp
            timestamp = int(timestamp_str)
            if time.time() - timestamp > max_age:
                return False

            # Verify signature
            expected = hmac.new(
                self.secret,
                f"{token_part}{timestamp_str}".encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected)

        except (ValueError, AttributeError):
            return False


def get_client_ip(handler) -> str:
    """
    Extract client IP from request handler.

    Handles X-Forwarded-For and X-Real-IP headers for proxied requests.

    Args:
        handler: HTTP request handler

    Returns:
        Client IP address
    """
    # Check for proxy headers
    forwarded_for = handler.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP (client IP)
        ip = forwarded_for.split(',')[0].strip()
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            pass

    real_ip = handler.headers.get('X-Real-IP')
    if real_ip:
        try:
            ipaddress.ip_address(real_ip)
            return real_ip
        except ValueError:
            pass

    # Fall back to socket address
    return handler.client_address[0]
