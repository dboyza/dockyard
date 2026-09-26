"""Dispatch API and dashboard; infrastructure is the learner's responsibility."""

import json
import os
import signal
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import psycopg
from redis.exceptions import RedisError

from database import database, initialize, queue

ROOT = Path(__file__).parent
server = None
STARTED = time.monotonic()


class Handler(BaseHTTPRequestHandler):
    def respond(self, payload, status=200, content_type="application/json"):
        body = payload.encode() if isinstance(payload, str) else json.dumps(payload, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            if self.path == "/healthz":
                self.respond({"service": "dispatch", "status": "ok", "release": (ROOT / "VERSION").read_text().strip(),
                              "environment": os.getenv("DISPATCH_ENV", "practice"), "uptime": round(time.monotonic() - STARTED, 1)})
            elif self.path == "/readyz":
                if time.monotonic() - STARTED < float(os.getenv("STARTUP_SECONDS", "0")):
                    self.respond({"ready": False, "reason": "Application is warming up"}, 503)
                    return
                with database() as connection:
                    initialize(connection)
                    connection.execute("SELECT 1")
                queue().ping()
                self.respond({"ready": True, "database": "available", "queue": "available"})
            elif self.path == "/jobs":
                with database() as connection:
                    initialize(connection)
                    jobs = connection.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 100").fetchall()
                self.respond({"jobs": jobs})
            elif self.path == "/metrics":
                with database() as connection:
                    initialize(connection)
                    counts = connection.execute("SELECT status,count(*) AS total FROM jobs GROUP BY status").fetchall()
                lines = ['# HELP dispatch_jobs Current jobs by status', '# TYPE dispatch_jobs gauge']
                lines.extend('dispatch_jobs{status="' + row['status'] + '"} ' + str(row['total']) for row in counts)
                self.respond('\n'.join(lines) + '\n', content_type="text/plain; version=0.0.4")
            elif self.path == "/":
                self.respond((ROOT / "dashboard.html").read_text(), content_type="text/html; charset=utf-8")
            else:
                self.respond({"error": "Not found"}, 404)
        except (psycopg.Error, RedisError, OSError) as error:
            print(json.dumps({"event": "dependency_error", "type": type(error).__name__}), flush=True)
            self.respond({"error": "A required dependency is unavailable"}, 503)

    def do_POST(self):
        if self.path != "/jobs":
            self.respond({"error": "Not found"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 100_000:
                raise ValueError("Send a small JSON body.")
            payload = json.loads(self.rfile.read(size))
            title = payload.get("title")
            if not isinstance(title, str) or not 1 <= len(title.strip()) <= 200:
                raise ValueError("Use a title of 1-200 characters.")
        except (ValueError, AttributeError, TypeError) as error:
            self.respond({"error": str(error)}, 400)
            return
        try:
            # Check the queue before accepting work; PostgreSQL remains the durable source.
            redis = queue()
            redis.ping()
            job = {"id": uuid.uuid4().hex, "title": title.strip(), "status": "queued"}
            with database() as connection:
                initialize(connection)
                connection.execute("INSERT INTO jobs(id,title) VALUES(%s,%s)", (job["id"], job["title"]))
            try:
                redis.lpush("dispatch:notifications", job["id"])
            except RedisError:
                # Workers also poll durable queued rows, so a lost notification loses no job.
                print(json.dumps({"event": "notification_deferred", "job": job["id"]}), flush=True)
            self.respond(job, 202)
        except (psycopg.Error, RedisError, OSError) as error:
            print(json.dumps({"event": "submit_error", "type": type(error).__name__}), flush=True)
            self.respond({"error": "Cannot accept work while a dependency is unavailable"}, 503)

    def do_DELETE(self):
        if not self.path.startswith("/jobs/"):
            self.respond({"error": "Not found"}, 404)
            return
        try:
            with database() as connection:
                connection.execute("DELETE FROM jobs WHERE id=%s", (self.path.removeprefix("/jobs/"),))
            self.respond({"deleted": True})
        except psycopg.Error:
            self.respond({"error": "Database unavailable"}, 503)


def terminate(signum, frame):
    if server:
        threading.Thread(target=server.shutdown, daemon=True).start()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    print(json.dumps({"event": "listening", "port": 8080}), flush=True)
    with ThreadingHTTPServer(("0.0.0.0", 8080), Handler) as server:
        server.serve_forever()
