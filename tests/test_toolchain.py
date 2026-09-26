"""Verify interrupted private downloads resume and never install corrupt bytes."""

import hashlib
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.toolchain import Toolchain


@pytest.fixture
def download(monkeypatch, tmp_path):
    payload = b"verified-private-tool\n" * 100
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            value = self.headers.get("Range")
            requests.append(value)
            offset = int(value.split("=")[1].split("-")[0]) if value else 0
            self.send_response(206 if value else 200)
            self.send_header("Content-Length", str(len(payload) - offset))
            self.end_headers()
            self.wfile.write(payload[offset:])

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(
        "dockyard.toolchain.MANIFEST",
        {
            "test": {
                "url": f"http://127.0.0.1:{server.server_port}/tool",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "path": "bin/test",
                "version": "1",
            }
        },
    )
    monkeypatch.setattr("dockyard.toolchain.platform.system", lambda: "Darwin")
    monkeypatch.setattr("dockyard.toolchain.platform.machine", lambda: "arm64")
    yield Toolchain(tmp_path), payload, requests
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_resume_then_verify_and_reuse_cache(download):
    toolchain, payload, requests = download
    (toolchain.root / "bin").mkdir()
    (toolchain.root / "bin/test.part").write_bytes(payload[:31])
    destination = toolchain.ensure("test", threading.Event(), lambda _: None)
    assert destination.read_bytes() == payload
    assert requests == ["bytes=31-"]
    assert destination.stat().st_mode & 0o111
    assert toolchain.ready("test")
    toolchain.ensure("test", threading.Event(), lambda _: None)
    assert len(requests) == 1


def test_corrupt_partial_never_replaces_installed_tool(download):
    toolchain, payload, _ = download
    (toolchain.root / "bin").mkdir()
    destination = toolchain.root / "bin/test"
    destination.write_bytes(b"older tool")
    destination.with_suffix(".part").write_bytes(b"corrupt")
    with pytest.raises(RuntimeErrorBase, match="integrity"):
        toolchain.ensure("test", threading.Event(), lambda _: None)
    assert destination.read_bytes() == b"older tool"
    assert not toolchain.ready("test")
    assert not destination.with_suffix(".part").exists()
    assert toolchain.ensure("test", threading.Event(), lambda _: None).read_bytes() == payload
