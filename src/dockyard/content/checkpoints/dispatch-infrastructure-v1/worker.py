"""Real background processing with durable queued rows and independent replicas."""

import hashlib
import json
import os
import signal
import socket
import threading

import psycopg
from psycopg.types.json import Jsonb
from redis.exceptions import RedisError

from database import database, initialize, queue

stopping = threading.Event()
identity = socket.gethostname()
signal.signal(signal.SIGTERM, lambda *_: stopping.set())
signal.signal(signal.SIGINT, lambda *_: stopping.set())

while not stopping.is_set():
    try:
        redis = queue()
        redis.set("dispatch:worker:" + identity, "ready", ex=10)
        redis.blpop("dispatch:notifications", timeout=1)
        with database() as connection:
            initialize(connection)
            job = connection.execute("SELECT id,title FROM jobs WHERE status='queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1").fetchone()
            if job:
                if stopping.wait(min(30, max(0, float(os.getenv("WORK_SECONDS", "0.2"))))):
                    continue
                result = {"normalized": job["title"].upper(), "sha256": hashlib.sha256(job["title"].encode()).hexdigest()}
                connection.execute("UPDATE jobs SET status='done',result=%s,worker=%s WHERE id=%s", (Jsonb(result), identity, job["id"]))
                print(json.dumps({"event": "job_completed", "job": job["id"], "worker": identity}), flush=True)
    except (psycopg.Error, RedisError, OSError) as error:
        print(json.dumps({"event": "dependency_retry", "type": type(error).__name__}), flush=True)
        stopping.wait(1)
