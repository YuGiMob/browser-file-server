"""
Tests for configuration module.
"""

import unittest
import tempfile
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.config import (
    Config, ServerConfig, SecurityConfig, FeaturesConfig, UIConfig, LoggingConfig,
    SSLConfig, RateLimitConfig, load_config_file, merge_configs, validate_config
)


class TestConfig(unittest.TestCase):
    """Test configuration classes."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        self.assertEqual(config.server.host, "127.0.0.1")
        self.assertEqual(config.server.port, 8080)
        self.assertEqual(config.server.root, "~")
        self.assertTrue(config.features.upload)
        self.assertTrue(config.features.delete)
        self.assertEqual(config.ui.theme, "dark")

    def test_server_config(self):
        """Test server configuration."""
        config = ServerConfig(host="0.0.0.0", port=9000, root="/tmp")
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.port, 9000)
        self.assertEqual(config.root, "/tmp")

    def test_features_config(self):
        """Test features configuration."""
        config = FeaturesConfig(upload=False, delete=False)
        self.assertFalse(config.upload)
        self.assertFalse(config.delete)
        self.assertTrue(config.edit)

    def test_ui_config(self):
        """Test UI configuration."""
        config = UIConfig(theme="light", show_hidden=True)
        self.assertEqual(config.theme, "light")
        self.assertTrue(config.show_hidden)

    def test_get_root_path(self):
        """Test get_root_path method."""
        config = Config(server=ServerConfig(root="~"))
        root = config.get_root_path()
        self.assertTrue(root.is_absolute())
        self.assertEqual(root, Path.home())

    def test_get_root_path_absolute(self):
        """Test get_root_path with absolute path."""
        config = Config(server=ServerConfig(root="/tmp"))
        root = config.get_root_path()
        self.assertEqual(root, Path("/tmp"))


class TestConfigFile(unittest.TestCase):
    """Test configuration file loading."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_nonexistent_config(self):
        """Test loading non-existent config file."""
        result = load_config_file("/nonexistent/config.yaml")
        self.assertEqual(result, {})

    def test_load_simple_config(self):
        """Test loading simple key=value config."""
        config_path = os.path.join(self.temp_dir, "config.txt")
        with open(config_path, "w") as f:
            f.write("server:\n")
            f.write("host=0.0.0.0\n")
            f.write("port=9000\n")

        result = load_config_file(config_path)
        self.assertIn("server", result)
        self.assertEqual(result["server"]["host"], "0.0.0.0")
        self.assertEqual(result["server"]["port"], 9000)


class TestConfigMerge(unittest.TestCase):
    """Test configuration merging."""

    def test_merge_empty(self):
        """Test merging with empty overrides."""
        defaults = {"server": {"host": "127.0.0.1", "port": 8080}}
        result = merge_configs(defaults, {})
        self.assertEqual(result, defaults)

    def test_merge_override(self):
        """Test merging with overrides."""
        defaults = {"server": {"host": "127.0.0.1", "port": 8080}}
        overrides = {"server": {"port": 9000}}
        result = merge_configs(defaults, overrides)
        self.assertEqual(result["server"]["host"], "127.0.0.1")
        self.assertEqual(result["server"]["port"], 9000)

    def test_merge_nested(self):
        """Test merging nested configs."""
        defaults = {"a": {"b": {"c": 1, "d": 2}}}
        overrides = {"a": {"b": {"c": 10}}}
        result = merge_configs(defaults, overrides)
        self.assertEqual(result["a"]["b"]["c"], 10)
        self.assertEqual(result["a"]["b"]["d"], 2)


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation."""

    def test_valid_config(self):
        """Test valid configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(server=ServerConfig(root=tmpdir))
            # Should not raise
            validate_config(config)

    def test_invalid_root(self):
        """Test invalid root directory."""
        config = Config(server=ServerConfig(root="/nonexistent/path"))
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_invalid_port(self):
        """Test invalid port number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                server=ServerConfig(root=tmpdir, port=99999)
            )
            with self.assertRaises(ValueError):
                validate_config(config)

    def test_invalid_port_zero(self):
        """Test port zero."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                server=ServerConfig(root=tmpdir, port=0)
            )
            with self.assertRaises(ValueError):
                validate_config(config)


if __name__ == "__main__":
    unittest.main()
