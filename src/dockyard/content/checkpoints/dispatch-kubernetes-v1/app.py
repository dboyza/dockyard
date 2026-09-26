"""Supplied Dispatch application: inspect the infrastructure, not application trivia."""

import json
import os
import signal
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).parent
server = None


class Handler(BaseHTTPRequestHandler):
    def respond(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            self.respond({"service": "dispatch", "status": "ok",
                          "release": (ROOT / "VERSION").read_text().strip(),
                          "environment": os.getenv("DISPATCH_ENV", "practice"),
                          "hostname": socket.gethostname()})
        elif self.path == "/dependency":
            endpoint = os.getenv("UPSTREAM_URL", "http://dependency:8080/healthz")
            try:
                with urlopen(endpoint, timeout=2) as response:
                    dependency = json.load(response)
                self.respond({"dependency": dependency, "connected": True})
            except Exception as error:
                self.respond({"connected": False, "reason": type(error).__name__}, 503)
        else:
            self.respond({"service": "dispatch", "message": "The Dispatch API is ready."})


def terminate(signum, frame):
    print(json.dumps({"event": "shutdown", "signal": signum}), flush=True)
    if server:
        threading.Thread(target=server.shutdown, daemon=True).start()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    print(json.dumps({"event": "listening", "address": "0.0.0.0:8080"}), flush=True)
    with ThreadingHTTPServer(("0.0.0.0", 8080), Handler) as server:
        server.serve_forever()
