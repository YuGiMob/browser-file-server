import unittest
import os
from pathlib import Path

from tests.base import BaseTest
from server.config import (
    Config, ServerConfig, SecurityConfig, FeaturesConfig, UIConfig, LoggingConfig,
    SSLConfig, RateLimitConfig, load_config_file, merge_configs, validate_config, apply_env_vars
)


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        config = Config()
        self.assertEqual(config.server.host, "127.0.0.1")
        self.assertEqual(config.server.port, 8080)
        self.assertEqual(config.server.root, "~")
        self.assertTrue(config.features.upload)
        self.assertTrue(config.features.delete)
        self.assertEqual(config.ui.theme, "dark")

    def test_server_config(self):
        config = ServerConfig(host="0.0.0.0", port=9000, root="/tmp")
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.port, 9000)
        self.assertEqual(config.root, "/tmp")

    def test_features_config(self):
        config = FeaturesConfig(upload=False, delete=False)
        self.assertFalse(config.upload)
        self.assertFalse(config.delete)
        self.assertTrue(config.edit)

    def test_ui_config(self):
        config = UIConfig(theme="light", show_hidden=True)
        self.assertEqual(config.theme, "light")
        self.assertTrue(config.show_hidden)

    def test_get_root_path(self):
        config = Config(server=ServerConfig(root="~"))
        root = config.get_root_path()
        self.assertTrue(root.is_absolute())
        self.assertEqual(root, Path.home())

    def test_get_root_path_absolute(self):
        config = Config(server=ServerConfig(root="/tmp"))
        root = config.get_root_path()
        self.assertEqual(root, Path("/tmp"))


class TestConfigFile(BaseTest):
    def test_load_nonexistent_config(self):
        result = load_config_file("/nonexistent/config.yaml")
        self.assertEqual(result, {})

    def test_load_simple_config(self):
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
    def test_merge_empty(self):
        defaults = {"server": {"host": "127.0.0.1", "port": 8080}}
        result = merge_configs(defaults, {})
        self.assertEqual(result, defaults)

    def test_merge_override(self):
        defaults = {"server": {"host": "127.0.0.1", "port": 8080}}
        overrides = {"server": {"port": 9000}}
        result = merge_configs(defaults, overrides)
        self.assertEqual(result["server"]["host"], "127.0.0.1")
        self.assertEqual(result["server"]["port"], 9000)

    def test_merge_nested(self):
        defaults = {"a": {"b": {"c": 1, "d": 2}}}
        overrides = {"a": {"b": {"c": 10}}}
        result = merge_configs(defaults, overrides)
        self.assertEqual(result["a"]["b"]["c"], 10)
        self.assertEqual(result["a"]["b"]["d"], 2)


class TestConfigValidation(unittest.TestCase):
    def test_valid_config(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(server=ServerConfig(root=tmpdir))
            validate_config(config)

    def test_invalid_root(self):
        config = Config(server=ServerConfig(root="/nonexistent/path"))
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_invalid_port(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                server=ServerConfig(root=tmpdir, port=99999)
            )
            with self.assertRaises(ValueError):
                validate_config(config)

    def test_invalid_port_zero(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                server=ServerConfig(root=tmpdir, port=0)
            )
            with self.assertRaises(ValueError):
                validate_config(config)


class TestApplyEnvVars(unittest.TestCase):
    def test_host_env_var(self):
        os.environ['FILESERVER_HOST'] = '0.0.0.0'
        try:
            config = {'server': {'host': '127.0.0.1'}}
            result = apply_env_vars(config)
            self.assertEqual(result['server']['host'], '0.0.0.0')
        finally:
            del os.environ['FILESERVER_HOST']

    def test_port_env_var(self):
        os.environ['FILESERVER_PORT'] = '9000'
        try:
            config = {'server': {'port': 8080}}
            result = apply_env_vars(config)
            self.assertEqual(result['server']['port'], 9000)
        finally:
            del os.environ['FILESERVER_PORT']

    def test_ssl_enabled_env_var(self):
        os.environ['FILESERVER_SSL_ENABLED'] = 'true'
        try:
            config = {'security': {'ssl': {'enabled': False}}}
            result = apply_env_vars(config)
            self.assertTrue(result['security']['ssl']['enabled'])
        finally:
            del os.environ['FILESERVER_SSL_ENABLED']

    def test_no_env_vars(self):
        config = {'server': {'host': '127.0.0.1', 'port': 8080}}
        result = apply_env_vars(config)
        self.assertEqual(result['server']['host'], '127.0.0.1')
        self.assertEqual(result['server']['port'], 8080)


if __name__ == "__main__":
    unittest.main()
