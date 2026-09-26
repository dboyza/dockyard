"""Immutable learner source checkpoints with explicit exclusions and provenance."""

from __future__ import annotations

import hashlib
import io
import json
import re
import uuid
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from dockyard.models import Assessment, Lab, Unit
from dockyard.workspace import atomic_write, snapshot

SOURCE_SUFFIXES = {
    ".py",
    ".sh",
    ".yaml",
    ".yml",
    ".json",
    ".md",
    ".txt",
    ".in",
    ".toml",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".conf",
    ".sql",
}
SOURCE_NAMES = {"Dockerfile", "Containerfile", "Makefile", "VERSION", ".dockerignore", ".gitignore"}


def checkpoint(
    directory: Path, lab: Lab, unit: Unit, assessment: Assessment, note: str
) -> dict[str, Any]:
    digest, files = snapshot(Path(lab.workspace))
    if digest != assessment.file_digest:
        raise ValueError("The workspace changed before its checkpoint could be recorded.")
    secrets = [
        value for key, value in lab.resources.items() if key in {"db_password", "bootstrap_token"}
    ]
    included: dict[str, bytes] = {}
    excluded: dict[str, str] = {}
    for name, body in files.items():
        path = Path(name)
        if (
            path.name.startswith(".env")
            or any(
                word in path.name.lower()
                for word in ("kubeconfig", "credential", "secret", "private-key", "backup", "dump")
            )
            or path.suffix.lower() in {".pem", ".key", ".p12", ".db", ".tar", ".gz", ".zip"}
        ):
            excluded[name] = "Credentials or runtime/backup data are excluded."
            continue
        if path.name not in SOURCE_NAMES and path.suffix not in SOURCE_SUFFIXES:
            excluded[name] = "Not an infrastructure source or documentation file."
            continue
        try:
            text = body.decode()
        except UnicodeDecodeError:
            excluded[name] = "Binary content is excluded."
            continue
        if any(secret and secret in text for secret in secrets) or re.search(
            r"(?m)^kind:\s*Secret\s*$", text
        ):
            excluded[name] = "Contains a known lab credential or Kubernetes Secret."
            continue
        included[name] = body
    for secret in secrets:
        if secret:
            note = note.replace(secret, "[redacted lab credential]")
    identity = uuid.uuid4().hex
    manifest = {
        "format": "dockyard-checkpoint",
        "version": 1,
        "id": identity,
        "unit_id": unit.id,
        "revision": unit.revision,
        "title": unit.title,
        "created_at": assessment.finished_at,
        "lab_id": lab.id,
        "independent": assessment.independent,
        "hints_used": assessment.hints_used,
        "reference_revealed": assessment.reference_revealed,
        "files": {name: hashlib.sha256(body).hexdigest() for name, body in included.items()},
        "excluded": excluded,
    }
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        archive.writestr("evidence.json", assessment.model_dump_json(indent=2))
        archive.writestr("observations.md", note)
        for name, body in included.items():
            archive.writestr("source/" + name, body)
    destination = directory / "checkpoints" / f"{identity}.zip"
    atomic_write(destination, buffer.getvalue())
    return {key: value for key, value in manifest.items() if key not in {"files", "excluded"}} | {
        "file_count": len(included),
        "excluded_count": len(excluded),
        "archive": destination.name,
    }
