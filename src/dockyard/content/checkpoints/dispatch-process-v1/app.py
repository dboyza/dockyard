"""Dispatch starts as a tiny HTTP API; infrastructure evolves around it."""

import json
import signal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            payload = {"service": "dispatch", "status": "ok"}
        elif self.path == "/":
            payload = {"service": "dispatch", "message": "Ready to accept jobs."}
        else:
            self.send_error(404)
            return
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def terminate(signum, frame):
    raise SystemExit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    print("Dispatch listening on 0.0.0.0:8080", flush=True)
    with ThreadingHTTPServer(("0.0.0.0", 8080), Handler) as server:
        server.serve_forever()
