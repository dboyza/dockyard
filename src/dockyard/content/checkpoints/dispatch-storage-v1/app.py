"""Dispatch adds durable jobs; all application code is supplied to the learner."""

import json
import os
import signal
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
DATA = Path(os.environ.get("DATA_DIR", "/data"))
server = None


@contextmanager
def database():
    DATA.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATA / "jobs.db", timeout=3)
    try:
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, title TEXT NOT NULL)")
            yield connection
    finally:
        connection.close()


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
            self.respond({"service": "dispatch", "status": "ok", "release": (ROOT / "VERSION").read_text().strip()})
        elif self.path == "/jobs":
            try:
                with database() as connection:
                    jobs = [{"id": row[0], "title": row[1]} for row in connection.execute("SELECT id,title FROM jobs ORDER BY id")]
                self.respond({"jobs": jobs})
            except (OSError, sqlite3.Error) as error:
                self.respond({"error": "Storage is unavailable", "reason": str(error)}, 503)
        elif self.path == "/":
            self.respond({"service": "dispatch", "message": "Create a job with POST /jobs."})
        else:
            self.respond({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path != "/jobs":
            self.respond({"error": "Not found"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 1_000_000:
                raise ValueError("Send a small JSON request body.")
            payload = json.loads(self.rfile.read(size))
            title = payload.get("title")
            if not isinstance(title, str) or not title.strip() or len(title) > 200:
                raise ValueError("A job needs a title of 1-200 characters.")
        except (ValueError, TypeError, AttributeError) as error:
            self.respond({"error": str(error)}, 400)
            return
        try:
            job = {"id": uuid.uuid4().hex, "title": title.strip()}
            with database() as connection:
                connection.execute("INSERT INTO jobs(id,title) VALUES(?,?)", (job["id"], job["title"]))
            self.respond(job, 201)
        except (OSError, sqlite3.Error) as error:
            self.respond({"error": "Storage is unavailable", "reason": str(error)}, 503)

    def do_DELETE(self):
        if not self.path.startswith("/jobs/"):
            self.respond({"error": "Not found"}, 404)
            return
        try:
            with database() as connection:
                connection.execute("DELETE FROM jobs WHERE id=?", (self.path.removeprefix("/jobs/"),))
            self.respond({"deleted": True})
        except (OSError, sqlite3.Error) as error:
            self.respond({"error": "Storage is unavailable", "reason": str(error)}, 503)


def terminate(signum, frame):
    print(json.dumps({"event": "shutdown", "signal": signum}), flush=True)
    if server:
        threading.Thread(target=server.shutdown, daemon=True).start()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    print(json.dumps({"event": "listening", "address": "0.0.0.0:8080"}), flush=True)
    with ThreadingHTTPServer(("0.0.0.0", 8080), Handler) as server:
        server.serve_forever()
