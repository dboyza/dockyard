"""Real HTTP contract tests, run inside the candidate image before publication."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from app import Handler

class ReleaseContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def test_health_identifies_built_release(self):
        with urllib.request.urlopen(self.url + "/healthz", timeout=3) as response:
            body = json.load(response)
        self.assertEqual(body["service"], "dispatch")
        self.assertEqual(body["release"], Path("VERSION").read_text().strip())

    def test_invalid_work_is_rejected_before_dependency_access(self):
        request = urllib.request.Request(self.url + "/jobs", data=b'{"title":""}', headers={"Content-Type":"application/json"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=3)
        self.assertEqual(caught.exception.code, 400)
        caught.exception.close()

unittest.main(verbosity=2)
