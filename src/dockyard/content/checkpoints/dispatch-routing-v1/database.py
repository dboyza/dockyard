"""Small supplied data layer shared by the API and worker."""

import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from redis import Redis


def database():
    secret_file = os.getenv("DB_PASSWORD_FILE")
    password = Path(secret_file).read_text().strip() if secret_file else os.getenv("DB_PASSWORD", "practice-only")
    return psycopg.connect(host=os.getenv("DB_HOST", "db"), port=int(os.getenv("DB_PORT", "5432")),
                          dbname=os.getenv("DB_NAME", "dispatch"), user=os.getenv("DB_USER", "dispatch"),
                          password=password, connect_timeout=3, row_factory=dict_row)


def queue():
    return Redis.from_url(os.getenv("REDIS_URL", "redis://queue:6379/0"), socket_connect_timeout=3,
                          socket_timeout=3, decode_responses=True)


def initialize(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
        result JSONB, worker TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
