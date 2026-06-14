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

from server.security import PathSecurity, RateLimiter, IPFilter, CSRFProtection


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


class TestCSRFProtection(unittest.TestCase):
    """Test CSRF protection."""

    def test_generate_token(self):
        """Test token generation."""
        csrf = CSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        self.assertIsNotNone(token)
        self.assertIn(".", token)

    def test_validate_token(self):
        """Test token validation."""
        csrf = CSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        self.assertTrue(csrf.validate_token(token))

    def test_invalid_token(self):
        """Test invalid token."""
        csrf = CSRFProtection(secret="test-secret")
        self.assertFalse(csrf.validate_token("invalid-token"))

    def test_tampered_token(self):
        """Test tampered token."""
        csrf = CSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        # Tamper with token
        tampered = token[:-5] + "XXXXX"
        self.assertFalse(csrf.validate_token(tampered))


if __name__ == "__main__":
    unittest.main()
