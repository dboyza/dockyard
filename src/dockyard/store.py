"""Transactional local progress, immutable attempts, and operation ownership."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from dockyard.models import Assessment, CheckStatus, Lab


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


class BusyError(RuntimeError):
    pass


class Store:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = directory / "progress.sqlite3"
        with self.connection() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > 1:
                raise RuntimeError("This profile needs a newer Dockyard version.")
            connection.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS labs (
                    id TEXT PRIMARY KEY, unit_id TEXT NOT NULL UNIQUE, body TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS progress (
                    unit_id TEXT PRIMARY KEY, viewed INTEGER NOT NULL DEFAULT 0,
                    hints INTEGER NOT NULL DEFAULT 0, reference INTEGER NOT NULL DEFAULT 0,
                    demonstrated INTEGER NOT NULL DEFAULT 0, practiced INTEGER NOT NULL DEFAULT 0,
                    revision INTEGER NOT NULL DEFAULT 0, review_at TEXT, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    id TEXT PRIMARY KEY, unit_id TEXT NOT NULL, created_at TEXT NOT NULL,
                    body TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS operations (
                    id TEXT PRIMARY KEY, lab_id TEXT NOT NULL, action TEXT NOT NULL,
                    state TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT ''
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_operation
                ON operations(lab_id) WHERE state IN ('queued', 'running', 'canceling');
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS notes (
                    unit_id TEXT PRIMARY KEY, body TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY, unit_id TEXT NOT NULL, created_at TEXT NOT NULL,
                    body TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS exams (
                    id TEXT PRIMARY KEY, body TEXT NOT NULL
                );
                PRAGMA user_version=1;
            """)

        self.path.chmod(0o600)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def save_lab(self, lab: Lab) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO labs(id,unit_id,body) VALUES(?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                (lab.id, lab.unit_id, lab.model_dump_json()),
            )

    def lab(self, unit_id: str) -> Lab | None:
        with self.connection() as connection:
            row = connection.execute("SELECT body FROM labs WHERE unit_id=?", (unit_id,)).fetchone()
        return Lab.model_validate_json(row[0]) if row else None

    def labs(self) -> list[Lab]:
        with self.connection() as connection:
            rows = connection.execute("SELECT body FROM labs ORDER BY unit_id").fetchall()
        return [Lab.model_validate_json(row[0]) for row in rows]

    def mark(self, unit_id: str, event: str, revision: int) -> None:
        if event not in {"viewed", "hints", "reference"}:
            raise ValueError("Unknown learning event.")
        with self.connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO progress(unit_id,revision,updated_at) VALUES(?,?,?)",
                (unit_id, revision, timestamp()),
            )
            # Column comes exclusively from the fixed set above.
            increment = "hints+1" if event == "hints" else "1"
            connection.execute(
                f"UPDATE progress SET {event}={increment},updated_at=? WHERE unit_id=?",
                (timestamp(), unit_id),
            )

    def progress(self) -> dict[str, dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM progress").fetchall()
        return {row["unit_id"]: dict(row) for row in rows}

    def start_attempt(self, unit_id: str, revision: int) -> int:
        key = f"attempt-number:{unit_id}"
        with self.connection() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            previous = int(json.loads(row[0])) if row else 1
            progress = connection.execute(
                "SELECT * FROM progress WHERE unit_id=?", (unit_id,)
            ).fetchone()
            connection.execute(
                "INSERT INTO settings(key,value) VALUES(?,?)",
                (
                    f"attempt-history:{unit_id}:{previous}",
                    json.dumps(
                        {
                            "finished_at": timestamp(),
                            "progress": dict(progress) if progress else {},
                        }
                    ),
                ),
            )
            connection.execute(
                "INSERT OR IGNORE INTO progress(unit_id,revision,updated_at) VALUES(?,?,?)",
                (unit_id, revision, timestamp()),
            )
            connection.execute(
                "UPDATE progress SET hints=0,reference=0,updated_at=? WHERE unit_id=?",
                (timestamp(), unit_id),
            )
            connection.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(previous + 1)),
            )
        return previous + 1

    def save_assessment(
        self, assessment: Assessment, checkpoint: dict[str, Any] | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO attempts(id,unit_id,created_at,body) VALUES(?,?,?,?)",
                (
                    assessment.id,
                    assessment.unit_id,
                    assessment.finished_at,
                    assessment.model_dump_json(),
                ),
            )
            connection.execute(
                "INSERT OR IGNORE INTO progress(unit_id,revision,updated_at) VALUES(?,?,?)",
                (assessment.unit_id, assessment.revision, timestamp()),
            )
            if checkpoint:
                connection.execute(
                    "INSERT INTO checkpoints(id,unit_id,created_at,body) VALUES(?,?,?,?)",
                    (
                        checkpoint["id"],
                        assessment.unit_id,
                        assessment.finished_at,
                        json.dumps(checkpoint),
                    ),
                )
            if assessment.status == CheckStatus.PASS:
                due = (
                    datetime.now(UTC) + timedelta(days=7 if assessment.independent else 1)
                ).isoformat()
                connection.execute(
                    "UPDATE progress SET practiced=1, demonstrated=CASE WHEN revision=? "
                    "THEN MAX(demonstrated,?) ELSE ? END,"
                    "revision=?,review_at=?,updated_at=? WHERE unit_id=?",
                    (
                        assessment.revision,
                        int(assessment.independent),
                        int(assessment.independent),
                        assessment.revision,
                        due,
                        timestamp(),
                        assessment.unit_id,
                    ),
                )

    def checkpoints(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT body FROM checkpoints ORDER BY created_at DESC"
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def attempts(self, unit_id: str) -> list[Assessment]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT body FROM attempts WHERE unit_id=? ORDER BY created_at DESC LIMIT 100",
                (unit_id,),
            ).fetchall()
        return [Assessment.model_validate_json(row[0]) for row in rows]

    def begin_operation(self, lab_id: str, action: str) -> str:
        operation_id = uuid.uuid4().hex
        try:
            with self.connection() as connection:
                connection.execute(
                    "INSERT INTO operations(id,lab_id,action,state,created_at,updated_at) "
                    "VALUES(?,?,?,'running',?,?)",
                    (operation_id, lab_id, action, timestamp(), timestamp()),
                )
        except sqlite3.IntegrityError as error:
            raise BusyError("This lab already has an operation in progress.") from error
        return operation_id

    def recover_operations(self, lab_id: str) -> None:
        """Called only while holding this lab's exclusive OS operation lock."""
        with self.connection() as connection:
            connection.execute(
                "UPDATE operations SET state='failed',updated_at=?,detail=? "
                "WHERE lab_id=? AND state IN ('queued','running','canceling')",
                (
                    timestamp(),
                    "The owning process ended. Inspect or prepare the preserved lab.",
                    lab_id,
                ),
            )

    def update_operation(self, operation_id: str, state: str, detail: str = "") -> None:
        if state not in {"queued", "running", "canceling", "done", "failed", "canceled"}:
            raise ValueError("Invalid operation state.")
        with self.connection() as connection:
            connection.execute(
                "UPDATE operations SET state=?,detail=?,updated_at=? WHERE id=?",
                (state, detail[-12000:], timestamp(), operation_id),
            )

    def operations(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM operations ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
        return [dict(row) for row in rows]

    def setting(self, key: str, default: Any = None) -> Any:
        with self.connection() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_setting(self, key: str, value: Any) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value)),
            )

    def save_note(self, unit_id: str, body: str) -> None:
        if len(body) > 50000:
            raise ValueError("Keep a unit note under 50,000 characters.")
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO notes(unit_id,body,updated_at) VALUES(?,?,?) "
                "ON CONFLICT(unit_id) DO UPDATE SET body=excluded.body,"
                "updated_at=excluded.updated_at",
                (unit_id, body, timestamp()),
            )

    def note(self, unit_id: str) -> str:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT body FROM notes WHERE unit_id=?", (unit_id,)
            ).fetchone()
        return str(row[0]) if row else ""
