import unittest
import tempfile
import os
import shutil
import threading
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from http.server import HTTPServer

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.config import Config, ServerConfig, SecurityConfig, FeaturesConfig, UIConfig, LoggingConfig, RateLimitConfig
from server.handler import create_handler_class
from server.storage import Storage


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def make_config(self, root=None, **overrides):
        return Config(
            server=ServerConfig(root=str(root or self.temp_dir)),
            security=SecurityConfig(rate_limit=RateLimitConfig(enabled=False)),
            features=FeaturesConfig(),
            ui=UIConfig(),
            logging=LoggingConfig(),
            **overrides
        )

    def make_storage(self, root=None, show_hidden=False):
        return Storage(root or self.temp_dir, show_hidden)


class BaseServerTest(BaseTest):
    def setUp(self):
        self.temp_dir = self.__class__.temp_dir

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.config = Config(
            server=ServerConfig(root=str(cls.temp_dir), port=0),
            security=SecurityConfig(rate_limit=RateLimitConfig(enabled=False)),
            features=FeaturesConfig(),
            ui=UIConfig(),
            logging=LoggingConfig(),
        )
        cls.handler_class = create_handler_class(cls.config)
        cls.server = HTTPServer(('127.0.0.1', 0), cls.handler_class)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        for _ in range(40):
            try:
                req = urllib.request.Request(f'http://127.0.0.1:{cls.port}/health')
                urllib.request.urlopen(req, timeout=1)
                break
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.25)
        else:
            raise RuntimeError('Server failed to start within 10 seconds')

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def _get(self, path):
        url = f'http://127.0.0.1:{self.port}{path}'
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.read().decode('utf-8'), response.status
        except urllib.error.HTTPError as e:
            return e.read().decode('utf-8'), e.code

    def _post(self, path, data=None):
        url = f'http://127.0.0.1:{self.port}{path}'
        if data:
            data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.read().decode('utf-8'), response.status
        except urllib.error.HTTPError as e:
            return e.read().decode('utf-8'), e.code
        except urllib.error.URLError:
            return '', 303
