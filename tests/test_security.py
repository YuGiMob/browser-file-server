"""
Tests for security module.
"""

import unittest
import tempfile
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.security import PathSecurity, RateLimiter, IPFilter, SecurityHeaders, get_client_ip


class TestPathSecurity(unittest.TestCase):
    """Test path security functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.root, ignore_errors=True)

    def test_safe_join_valid(self):
        """Test safe_join with valid paths."""
        result = PathSecurity.safe_join(self.root, "test.txt")
        self.assertEqual(result, self.root / "test.txt")

    def test_safe_join_subdirectory(self):
        """Test safe_join with subdirectory."""
        result = PathSecurity.safe_join(self.root, "subdir/test.txt")
        self.assertEqual(result, self.root / "subdir" / "test.txt")

    def test_safe_join_traversal(self):
        """Test safe_join prevents path traversal."""
        with self.assertRaises(ValueError):
            PathSecurity.safe_join(self.root, "../etc/passwd")

    def test_safe_join_traversal_encoded(self):
        """Test safe_join prevents encoded path traversal."""
        with self.assertRaises(ValueError):
            PathSecurity.safe_join(self.root, "..%2Fetc%2Fpasswd")

    def test_safe_join_null_byte(self):
        """Test safe_join prevents null bytes."""
        with self.assertRaises(ValueError):
            PathSecurity.safe_join(self.root, "test\x00.txt")

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        self.assertEqual(PathSecurity.sanitize_filename("test.txt"), "test.txt")
        # Path separators are replaced with underscores
        result = PathSecurity.sanitize_filename("../../../etc/passwd")
        self.assertNotIn("/", result)
        self.assertNotIn("..", result)
        self.assertEqual(PathSecurity.sanitize_filename("test/file.txt"), "test_file.txt")

    def test_sanitize_filename_empty(self):
        """Test sanitization of empty filename."""
        result = PathSecurity.sanitize_filename("")
        self.assertEqual(result, "unnamed")

    def test_is_safe_path(self):
        """Test path safety check."""
        self.assertTrue(PathSecurity.is_safe_path("test.txt"))
        self.assertTrue(PathSecurity.is_safe_path("subdir/test.txt"))
        self.assertFalse(PathSecurity.is_safe_path("../etc/passwd"))


class TestRateLimiter(unittest.TestCase):
    """Test rate limiter."""

    def test_allow_within_limit(self):
        """Test requests within rate limit."""
        limiter = RateLimiter(requests_per_minute=60, burst=10)

        # Should allow burst
        for _ in range(10):
            allowed, _ = limiter.is_allowed("192.168.1.1")
            self.assertTrue(allowed)

    def test_deny_over_limit(self):
        """Test requests over rate limit."""
        limiter = RateLimiter(requests_per_minute=1, burst=1)

        # First request should be allowed
        allowed, _ = limiter.is_allowed("192.168.1.1")
        self.assertTrue(allowed)

        # Second request should be denied
        allowed, retry_after = limiter.is_allowed("192.168.1.1")
        self.assertFalse(allowed)
        self.assertIsNotNone(retry_after)

    def test_different_ips(self):
        """Test rate limiting per IP."""
        limiter = RateLimiter(requests_per_minute=1, burst=1)

        # Different IPs should have separate limits
        allowed1, _ = limiter.is_allowed("192.168.1.1")
        allowed2, _ = limiter.is_allowed("192.168.1.2")

        self.assertTrue(allowed1)
        self.assertTrue(allowed2)


class TestIPFilter(unittest.TestCase):
    """Test IP filter."""

    def test_allow_all(self):
        """Test allowing all IPs when no filter set."""
        ip_filter = IPFilter()
        self.assertTrue(ip_filter.is_allowed("192.168.1.1"))

    def test_allow_whitelist(self):
        """Test IP whitelist."""
        ip_filter = IPFilter(allowed_ips=["192.168.1.1", "10.0.0.0/8"])
        self.assertTrue(ip_filter.is_allowed("192.168.1.1"))
        self.assertTrue(ip_filter.is_allowed("10.0.0.1"))
        self.assertFalse(ip_filter.is_allowed("172.16.0.1"))

    def test_block_blacklist(self):
        """Test IP blacklist."""
        ip_filter = IPFilter(blocked_ips=["192.168.1.1"])
        self.assertFalse(ip_filter.is_allowed("192.168.1.1"))
        self.assertTrue(ip_filter.is_allowed("192.168.1.2"))


class TestSecurityHeaders(unittest.TestCase):
    """Test security headers."""

    def test_get_headers_default(self):
        """Test default security headers."""
        headers = SecurityHeaders.get_headers()
        self.assertIn('X-Content-Type-Options', headers)
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn('X-Frame-Options', headers)
        self.assertEqual(headers['X-Frame-Options'], 'DENY')
        self.assertIn('Content-Security-Policy', headers)

    def test_get_headers_no_csp(self):
        """Test headers without CSP."""
        headers = SecurityHeaders.get_headers(csp_enabled=False)
        self.assertNotIn('Content-Security-Policy', headers)
        self.assertIn('X-Content-Type-Options', headers)

    def test_get_headers_hsts(self):
        """Test headers with HSTS."""
        headers = SecurityHeaders.get_headers(hsts_enabled=True)
        self.assertIn('Strict-Transport-Security', headers)
        self.assertIn('max-age', headers['Strict-Transport-Security'])


class TestGetClientIp(unittest.TestCase):
    """Test client IP extraction."""

    def _make_handler(self, headers=None, client_addr=('127.0.0.1', 12345)):
        """Create a mock handler."""
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = headers or {}
        handler.client_address = client_addr
        return handler

    def test_direct_connection(self):
        """Test IP from direct connection."""
        handler = self._make_handler()
        self.assertEqual(get_client_ip(handler), '127.0.0.1')

    def test_x_forwarded_for(self):
        """Test IP from X-Forwarded-For header."""
        handler = self._make_handler(headers={'X-Forwarded-For': '10.0.0.1, 192.168.1.1'})
        self.assertEqual(get_client_ip(handler), '10.0.0.1')

    def test_x_real_ip(self):
        """Test IP from X-Real-IP header."""
        handler = self._make_handler(headers={'X-Real-IP': '10.0.0.2'})
        self.assertEqual(get_client_ip(handler), '10.0.0.2')

    def test_forwarded_for_takes_priority(self):
        """Test X-Forwarded-For takes priority over X-Real-IP."""
        handler = self._make_handler(headers={
            'X-Forwarded-For': '10.0.0.1',
            'X-Real-IP': '10.0.0.2'
        })
        self.assertEqual(get_client_ip(handler), '10.0.0.1')

    def test_invalid_forwarded_for(self):
        """Test fallback when X-Forwarded-For has invalid IP."""
        handler = self._make_handler(headers={'X-Forwarded-For': 'not-an-ip'})
        self.assertEqual(get_client_ip(handler), '127.0.0.1')


class TestRateLimiterCleanup(unittest.TestCase):
    """Test rate limiter cleanup."""

    def test_cleanup_removes_old_entries(self):
        """Test that cleanup removes old entries."""
        limiter = RateLimiter(requests_per_minute=60, burst=10)
        # Add some entries
        limiter.is_allowed('192.168.1.1')
        limiter.is_allowed('192.168.1.2')
        self.assertEqual(len(limiter.buckets), 2)
        # Cleanup with max_age=0 should remove all
        limiter.cleanup(max_age=0)
        self.assertEqual(len(limiter.buckets), 0)


class TestCSRFProtection(unittest.TestCase):
    """Test CSRF token validation."""

    def setUp(self):
        """Set up test fixtures."""
        from unittest.mock import MagicMock
        import hmac
        import hashlib
        import time
        self.hmac = hmac
        self.hashlib = hashlib
        self.time = time

    def _make_handler(self, secret=b'test-secret-32-bytes-long!', client_addr=('127.0.0.1', 12345)):
        """Create a mock handler with CSRF secret."""
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler._csrf_secret = secret
        handler.client_address = client_addr
        return handler

    def _generate_token(self, handler, offset=0):
        """Generate a CSRF token for testing."""
        window = str(int(self.time.time()) // 3600 + offset)
        client_ip = handler.client_address[0]
        return self.hmac.new(
            handler._csrf_secret,
            f"{client_ip}:{window}".encode(),
            self.hashlib.sha256
        ).hexdigest()[:32]

    def test_validate_valid_token(self):
        """Test validation of a valid CSRF token."""
        from server.handler import FileServerHandler
        handler = self._make_handler()
        token = self._generate_token(handler)
        result = FileServerHandler._validate_csrf_token(handler, token)
        self.assertTrue(result)

    def test_validate_invalid_token(self):
        """Test validation of an invalid CSRF token."""
        from server.handler import FileServerHandler
        handler = self._make_handler()
        result = FileServerHandler._validate_csrf_token(handler, 'invalid-token')
        self.assertFalse(result)

    def test_validate_empty_token(self):
        """Test validation of an empty CSRF token."""
        from server.handler import FileServerHandler
        handler = self._make_handler()
        result = FileServerHandler._validate_csrf_token(handler, '')
        self.assertFalse(result)

    def test_validate_token_previous_window(self):
        """Test validation of a token from the previous time window."""
        from server.handler import FileServerHandler
        handler = self._make_handler()
        token = self._generate_token(handler, offset=-1)
        result = FileServerHandler._validate_csrf_token(handler, token)
        self.assertTrue(result)

    def test_validate_token_wrong_secret(self):
        """Test validation fails with wrong secret."""
        from server.handler import FileServerHandler
        handler = self._make_handler(secret=b'different-secret-value-here!')
        token = self._generate_token(handler)
        # Validate with a handler that has a different secret
        validator = self._make_handler(secret=b'another-secret-value-here!')
        result = FileServerHandler._validate_csrf_token(validator, token)
        self.assertFalse(result)

    def test_validate_token_wrong_ip(self):
        """Test validation fails with different client IP."""
        from server.handler import FileServerHandler
        handler = self._make_handler(client_addr=('10.0.0.1', 12345))
        token = self._generate_token(handler)
        # Validate from a different IP
        validator = self._make_handler(client_addr=('10.0.0.2', 12345))
        result = FileServerHandler._validate_csrf_token(validator, token)
        self.assertFalse(result)
if __name__ == "__main__":
    unittest.main()
