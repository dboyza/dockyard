"""Focused incident observations with explicit expected failure results."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from contextlib import suppress
from typing import Any

from dockyard.probes.docker import inspect, request, storage
from dockyard.process import run


def permissions() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(
        ("mount", "roundtrip", "durable", "preserved", "nonroot"), False
    )
    with suppress(RuntimeError, ValueError, KeyError, OSError, sqlite3.Error):
        result.update(storage("volume"))
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        seed = "incident-" + os.environ["DOCKYARD_LAB"]
        result["preserved"] = {"id": seed, "title": "Keep this original job"} in request("/jobs")[
            "jobs"
        ]
        container = inspect("container", os.environ["DOCKYARD_CONTAINER"])
        state = run(
            [
                "docker",
                "exec",
                container["Id"],
                "python",
                "-c",
                "import json,os; s=os.stat('/data/jobs.db'); "
                "print(json.dumps({'uid':os.getuid(),'owner':s.st_uid,'mode':s.st_mode & 0o777}))",
            ]
        )
        details = json.loads(state.stdout)
        result["nonroot"] = bool(
            details["uid"] == details["owner"] == 10001 and details["mode"] & 0o022 == 0
        )
        result["_details"] = details
    return result


if __name__ == "__main__":
    if sys.argv[1:] != ["permissions"]:
        raise SystemExit("Unknown packaged incident observation.")
    print(json.dumps(permissions()))
