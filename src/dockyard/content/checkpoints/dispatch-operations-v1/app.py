"""Dispatch API and dashboard; infrastructure is the learner's responsibility."""

import json
import os
import signal
import socket
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
METRIC_LOCK = threading.Lock()
REQUESTS = {}
BUCKETS = [0.05, 0.1, 0.25, 0.5, 1, 2, 5]
HISTOGRAM = dict.fromkeys(BUCKETS, 0)
TOTAL_DURATION = 0.0
TOTAL_REQUESTS = 0


def metrics():
    with METRIC_LOCK:
        lines = ['# TYPE dispatch_http_requests_total counter', '# TYPE dispatch_http_request_duration_seconds histogram']
        for (route, status), count in REQUESTS.items():
            lines.append(f'dispatch_http_requests_total{{route="{route}",status="{status}"}} {count}')
        for bound, count in HISTOGRAM.items():
            lines.append(f'dispatch_http_request_duration_seconds_bucket{{le="{bound}"}} {count}')
        lines += [f'dispatch_http_request_duration_seconds_bucket{{le="+Inf"}} {TOTAL_REQUESTS}',
                  f'dispatch_http_request_duration_seconds_count {TOTAL_REQUESTS}',
                  f'dispatch_http_request_duration_seconds_sum {TOTAL_DURATION}']
    return '\n'.join(lines) + '\n'



class Handler(BaseHTTPRequestHandler):
    def respond(self, payload, status=200, content_type="application/json"):
        global TOTAL_DURATION, TOTAL_REQUESTS
        request_id = uuid.uuid4().hex
        duration = time.perf_counter() - getattr(self, 'request_started', time.perf_counter())
        route = self.path if self.path in {'/jobs', '/readyz', '/healthz', '/config', '/startupz', '/'} else '/other'
        if self.path == '/jobs' and self.command == 'GET':
            with METRIC_LOCK:
                REQUESTS[(route, str(status))] = REQUESTS.get((route, str(status)), 0) + 1
                TOTAL_REQUESTS += 1
                TOTAL_DURATION += duration
                for bound in BUCKETS:
                    if duration <= bound: HISTOGRAM[bound] += 1
            print(json.dumps({'event':'http_request','request_id':request_id,'route':route,'status':status,
                              'duration_seconds':round(duration,6),'pod':socket.gethostname()}), flush=True)
        body = payload.encode() if isinstance(payload, str) else json.dumps(payload, default=str).encode()
        self.send_response(status)
        self.send_header("X-Request-ID", request_id)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.request_started = time.perf_counter()
        try:
            if self.path == "/healthz":
                self.respond({"service": "dispatch", "status": "ok", "release": (ROOT / "VERSION").read_text().strip(),
                              "hostname": socket.gethostname(), "environment": os.getenv("DISPATCH_ENV", "practice"), "uptime": round(time.monotonic() - STARTED, 1)})
            elif self.path == "/startupz":
                warmed = time.monotonic() - STARTED >= float(os.getenv("STARTUP_SECONDS", "0"))
                self.respond({"started": warmed}, 200 if warmed else 503)
            elif self.path == "/config":
                self.respond({"environment": os.getenv("DISPATCH_ENV", "practice"), "banner": Path("/config/banner.txt").read_text().strip()})
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
                delay = min(2000, max(0, int(Path('/config/delay_ms').read_text().strip())))
                time.sleep(delay / 1000)
                with database() as connection:
                    initialize(connection)
                    jobs = connection.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 100").fetchall()
                self.respond({"jobs": jobs})
            elif self.path == "/metrics":
                self.respond(metrics(), content_type="text/plain; version=0.0.4")
            elif self.path == "/":
                self.respond((ROOT / "dashboard.html").read_text(), content_type="text/html; charset=utf-8")
            else:
                self.respond({"error": "Not found"}, 404)
        except (psycopg.Error, RedisError, OSError) as error:
            print(json.dumps({"event": "dependency_error", "type": type(error).__name__}), flush=True)
            self.respond({"error": "A required dependency is unavailable"}, 503)

    def do_POST(self):
        self.request_started = time.perf_counter()
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
        self.request_started = time.perf_counter()
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
        print(json.dumps({"event": "terminating", "signal": signum}), flush=True)
        threading.Thread(target=server.shutdown, daemon=True).start()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    print(json.dumps({"event": "listening", "port": 8080}), flush=True)
    with ThreadingHTTPServer(("0.0.0.0", 8080), Handler) as server:
        server.serve_forever()
