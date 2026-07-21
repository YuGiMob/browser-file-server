import unittest
import os
from pathlib import Path

from tests.base import BaseTest
from server.security import PathSecurity, RateLimiter, IPFilter, SecurityHeaders, get_client_ip


class TestPathSecurity(BaseTest):
    def test_safe_join_valid(self):
        result = PathSecurity.safe_join(self.temp_dir, "test.txt")
        self.assertEqual(result, self.temp_dir / "test.txt")

    def test_safe_join_subdirectory(self):
        result = PathSecurity.safe_join(self.temp_dir, "subdir/test.txt")
        self.assertEqual(result, self.temp_dir / "subdir" / "test.txt")

    def test_safe_join_traversal(self):
        with self.assertRaises(ValueError):
            PathSecurity.safe_join(self.temp_dir, "../etc/passwd")

    def test_safe_join_traversal_encoded(self):
        with self.assertRaises(ValueError):
            PathSecurity.safe_join(self.temp_dir, "..%2Fetc%2Fpasswd")

    def test_safe_join_null_byte(self):
        with self.assertRaises(ValueError):
            PathSecurity.safe_join(self.temp_dir, "test\x00.txt")

    def test_sanitize_filename(self):
        self.assertEqual(PathSecurity.sanitize_filename("test.txt"), "test.txt")
        result = PathSecurity.sanitize_filename("../../../etc/passwd")
        self.assertNotIn("/", result)
        self.assertNotIn("..", result)
        self.assertEqual(PathSecurity.sanitize_filename("test/file.txt"), "test_file.txt")

    def test_sanitize_filename_empty(self):
        result = PathSecurity.sanitize_filename("")
        self.assertEqual(result, "unnamed")

    def test_is_safe_path(self):
        self.assertTrue(PathSecurity.is_safe_path("test.txt"))
        self.assertTrue(PathSecurity.is_safe_path("subdir/test.txt"))
        self.assertFalse(PathSecurity.is_safe_path("../etc/passwd"))

    def test_safe_join_dangerous_chars(self):
        with self.assertRaises(ValueError):
            PathSecurity.safe_join(self.temp_dir, "test\x00.txt")

    def test_safe_join_reserved_name(self):
        with self.assertRaises(ValueError):
            PathSecurity.safe_join(self.temp_dir, "CON")
        with self.assertRaises(ValueError):
            PathSecurity.safe_join(self.temp_dir, "COM1.txt")

    def test_safe_join_empty_path(self):
        result = PathSecurity.safe_join(self.temp_dir, "")
        self.assertEqual(result, self.temp_dir)

    def test_sanitize_filename_dangerous(self):
        result = PathSecurity.sanitize_filename("test\x00.txt")
        self.assertEqual(result, "test.txt")
        result = PathSecurity.sanitize_filename("  .  ")
        self.assertEqual(result, "unnamed")
        result = PathSecurity.sanitize_filename("a" * 300 + ".txt")
        self.assertEqual(len(result), 255)  # max 255 chars total
        self.assertTrue(result.endswith('.txt'))

class TestRateLimiter(unittest.TestCase):
    def test_allow_within_limit(self):
        limiter = RateLimiter(requests_per_minute=60, burst=10)
        for _ in range(10):
            allowed, _ = limiter.is_allowed("192.168.1.1")
            self.assertTrue(allowed)

    def test_deny_over_limit(self):
        limiter = RateLimiter(requests_per_minute=1, burst=1)
        allowed, _ = limiter.is_allowed("192.168.1.1")
        self.assertTrue(allowed)
        allowed, retry_after = limiter.is_allowed("192.168.1.1")
        self.assertFalse(allowed)
        self.assertIsNotNone(retry_after)

    def test_different_ips(self):
        limiter = RateLimiter(requests_per_minute=1, burst=1)
        allowed1, _ = limiter.is_allowed("192.168.1.1")
        allowed2, _ = limiter.is_allowed("192.168.1.2")
        self.assertTrue(allowed1)
        self.assertTrue(allowed2)


class TestIPFilter(unittest.TestCase):
    def test_allow_all(self):
        ip_filter = IPFilter()
        self.assertTrue(ip_filter.is_allowed("192.168.1.1"))

    def test_allow_whitelist(self):
        ip_filter = IPFilter(allowed_ips=["192.168.1.1", "10.0.0.0/8"])
        self.assertTrue(ip_filter.is_allowed("192.168.1.1"))
        self.assertTrue(ip_filter.is_allowed("10.0.0.1"))
        self.assertFalse(ip_filter.is_allowed("172.16.0.1"))

    def test_block_blacklist(self):
        ip_filter = IPFilter(blocked_ips=["192.168.1.1"])
        self.assertFalse(ip_filter.is_allowed("192.168.1.1"))
        self.assertTrue(ip_filter.is_allowed("192.168.1.2"))


class TestSecurityHeaders(unittest.TestCase):
    def test_get_headers_default(self):
        headers = SecurityHeaders.get_headers()
        self.assertIn('X-Content-Type-Options', headers)
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn('X-Frame-Options', headers)
        self.assertEqual(headers['X-Frame-Options'], 'DENY')
        self.assertIn('Content-Security-Policy', headers)

    def test_get_headers_no_csp(self):
        headers = SecurityHeaders.get_headers(csp_enabled=False)
        self.assertNotIn('Content-Security-Policy', headers)
        self.assertIn('X-Content-Type-Options', headers)

    def test_get_headers_hsts(self):
        headers = SecurityHeaders.get_headers(hsts_enabled=True)
        self.assertIn('Strict-Transport-Security', headers)
        self.assertIn('max-age', headers['Strict-Transport-Security'])


class TestGetClientIp(unittest.TestCase):
    def _make_handler(self, headers=None, client_addr=('127.0.0.1', 12345)):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = headers or {}
        handler.client_address = client_addr
        return handler

    def test_direct_connection(self):
        handler = self._make_handler()
        self.assertEqual(get_client_ip(handler), '127.0.0.1')

    def test_x_forwarded_for(self):
        handler = self._make_handler(headers={'X-Forwarded-For': '10.0.0.1, 192.168.1.1'})
        self.assertEqual(get_client_ip(handler), '10.0.0.1')

    def test_x_real_ip(self):
        handler = self._make_handler(headers={'X-Real-IP': '10.0.0.2'})
        self.assertEqual(get_client_ip(handler), '10.0.0.2')

    def test_forwarded_for_takes_priority(self):
        handler = self._make_handler(headers={
            'X-Forwarded-For': '10.0.0.1',
            'X-Real-IP': '10.0.0.2'
        })
        self.assertEqual(get_client_ip(handler), '10.0.0.1')

    def test_invalid_forwarded_for(self):
        handler = self._make_handler(headers={'X-Forwarded-For': 'not-an-ip'})
        self.assertEqual(get_client_ip(handler), '127.0.0.1')


class TestRateLimiterCleanup(unittest.TestCase):
    def test_cleanup_removes_old_entries(self):
        limiter = RateLimiter(requests_per_minute=60, burst=10)
        limiter.is_allowed('192.168.1.1')
        limiter.is_allowed('192.168.1.2')
        self.assertEqual(len(limiter.buckets), 2)
        limiter.cleanup(max_age=0)
        self.assertEqual(len(limiter.buckets), 0)


class TestCSRFProtection(unittest.TestCase):
    def setUp(self):
        from unittest.mock import MagicMock
        import hmac
        import hashlib
        import time
        self.hmac = hmac
        self.hashlib = hashlib
        self.time = time

    def _make_handler(self, secret=b'test-secret-32-bytes-long!', client_addr=('127.0.0.1', 12345)):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler._csrf_secret = secret
        handler.client_address = client_addr
        handler._get_csrf_secret = lambda: secret
        return handler

    def _generate_token(self, handler, offset=0):
        window = str(int(self.time.time()) // 3600 + offset)
        client_ip = handler.client_address[0]
        return self.hmac.new(
            handler._csrf_secret,
            f"{client_ip}:{window}".encode(),
            self.hashlib.sha256
        ).hexdigest()[:32]

    def test_validate_valid_token(self):
        from server.handler import FileServerHandler
        handler = self._make_handler()
        token = self._generate_token(handler)
        result = FileServerHandler._validate_csrf_token(handler, token)
        self.assertTrue(result)

    def test_validate_invalid_token(self):
        from server.handler import FileServerHandler
        handler = self._make_handler()
        result = FileServerHandler._validate_csrf_token(handler, 'invalid-token')
        self.assertFalse(result)

    def test_validate_empty_token(self):
        from server.handler import FileServerHandler
        handler = self._make_handler()
        result = FileServerHandler._validate_csrf_token(handler, '')
        self.assertFalse(result)

    def test_validate_token_previous_window(self):
        from server.handler import FileServerHandler
        handler = self._make_handler()
        token = self._generate_token(handler, offset=-1)
        result = FileServerHandler._validate_csrf_token(handler, token)
        self.assertTrue(result)

    def test_validate_token_wrong_secret(self):
        from server.handler import FileServerHandler
        handler = self._make_handler(secret=b'different-secret-value-here!')
        token = self._generate_token(handler)
        validator = self._make_handler(secret=b'another-secret-value-here!')
        result = FileServerHandler._validate_csrf_token(validator, token)
        self.assertFalse(result)

    def test_validate_token_wrong_ip(self):
        from server.handler import FileServerHandler
        handler = self._make_handler(client_addr=('10.0.0.1', 12345))
        token = self._generate_token(handler)
        validator = self._make_handler(client_addr=('10.0.0.2', 12345))
        result = FileServerHandler._validate_csrf_token(validator, token)
        self.assertFalse(result)


class TestRateLimiterExtended(unittest.TestCase):
    def test_token_refill(self):
        limiter = RateLimiter(requests_per_minute=60, burst=5)
        for _ in range(5):
            allowed, _ = limiter.is_allowed('10.0.0.1')
            self.assertTrue(allowed)
        allowed, _ = limiter.is_allowed('10.0.0.1')
        self.assertFalse(allowed)
        # Wait for token refill
        import time
        time.sleep(1.1)
        allowed, _ = limiter.is_allowed('10.0.0.1')
        self.assertTrue(allowed)

    def test_cleanup_no_entries(self):
        limiter = RateLimiter(requests_per_minute=60, burst=10)
        limiter.cleanup()
        self.assertEqual(len(limiter.buckets), 0)


class TestIPFilterExtended(unittest.TestCase):
    def test_invalid_ip(self):
        ip_filter = IPFilter()
        self.assertFalse(ip_filter.is_allowed('not-an-ip'))

    def test_blocked_network(self):
        ip_filter = IPFilter(blocked_ips=['10.0.0.0/8'])
        self.assertFalse(ip_filter.is_allowed('10.0.0.1'))
        self.assertTrue(ip_filter.is_allowed('192.168.1.1'))

    def test_allowed_network(self):
        ip_filter = IPFilter(allowed_ips=['192.168.0.0/16'])
        self.assertTrue(ip_filter.is_allowed('192.168.1.1'))
        self.assertFalse(ip_filter.is_allowed('10.0.0.1'))


class TestSecurityHeadersExtended(unittest.TestCase):
    def test_all_headers_present(self):
        headers = SecurityHeaders.get_headers()
        self.assertIn('X-Content-Type-Options', headers)
        self.assertIn('X-Frame-Options', headers)
        self.assertIn('X-XSS-Protection', headers)
        self.assertIn('Referrer-Policy', headers)
        self.assertIn('Permissions-Policy', headers)
        self.assertIn('Content-Security-Policy', headers)

    def test_csp_values(self):
        headers = SecurityHeaders.get_headers()
        csp = headers['Content-Security-Policy']
        self.assertIn("default-src 'self'", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertIn("style-src 'self'", csp)
        self.assertIn("img-src 'self'", csp)


class TestGetClientIpExtended(unittest.TestCase):
    def _make_handler(self, headers=None, client_addr=('127.0.0.1', 12345)):
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.headers = headers or {}
        handler.client_address = client_addr
        return handler

    def test_empty_headers(self):
        handler = self._make_handler(headers={})
        self.assertEqual(get_client_ip(handler), '127.0.0.1')

    def test_invalid_real_ip(self):
        handler = self._make_handler(headers={'X-Real-IP': 'not-an-ip'})
        self.assertEqual(get_client_ip(handler), '127.0.0.1')

    def test_ipv6_client(self):
        handler = self._make_handler(client_addr=('::1', 12345))
        self.assertEqual(get_client_ip(handler), '::1')


if __name__ == "__main__":
    unittest.main()
