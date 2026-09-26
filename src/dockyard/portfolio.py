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

import yaml

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


def portable_yaml(text: str) -> tuple[str, list[str]]:
    """Keep authored documents intact; omit only documents containing literal Secret data."""
    safe_helm = re.compile(
        r'{{-?\s*(?:required\s+"[^"\n]*"\s+)?\.Values\.[A-Za-z0-9_.]+(?:\s*\|\s*(?:quote|b64enc|toString))*\s*-?}}'
    )
    kept = []
    removed = []
    for index, document in enumerate(re.split(r"(?m)^---[ \t]*(?:#.*)?\r?\n", text), 1):
        tokens: dict[str, str] = {}

        def placeholder(match: re.Match[str], known: dict[str, str] = tokens) -> str:
            key = "DOCKYARDTEMPLATE" + uuid.uuid4().hex
            known[key] = match.group()
            return key

        # Parse scalar Helm expressions as inert markers, without evaluating the template.
        parsed = re.sub(r"{{[^{}\n]+}}", placeholder, document)
        try:
            value = yaml.safe_load(parsed)
        except yaml.YAMLError:
            if re.search(r"\b(?:Secret|client-key-data|private-key)\b", document):
                removed.append(
                    f"Document {index}: credential-bearing template could not be inspected."
                )
                continue
            kept.append(document)
            continue

        def private(node: Any, known: dict[str, str] = tokens) -> bool:
            if isinstance(node, list):
                return any(private(item) for item in node)
            if not isinstance(node, dict):
                return False
            if node.get("kind") == "Secret":
                fields = [node.get(key, {}) for key in ("data", "stringData")]
                values = [
                    item
                    for mapping in fields
                    if isinstance(mapping, dict)
                    for item in mapping.values()
                ]
                if not values or any(not isinstance(mapping, dict) for mapping in fields):
                    return True
                return any(
                    not isinstance(item, str)
                    or not (
                        item in known
                        and safe_helm.fullmatch(known[item])
                        or re.fullmatch(r"\$\{[A-Z][A-Z0-9_]*\}", item)
                    )
                    for item in values
                )
            return any(private(item) for item in node.values())

        if private(value):
            removed.append(
                f"Document {index}: literal Kubernetes Secret data requires regeneration."
            )
        else:
            kept.append(document)
    return ("---\n".join(kept) if removed else text), removed


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
    transformed: dict[str, list[str]] = {}
    for name, body in files.items():
        path = Path(name)
        if (
            path.name.startswith(".env")
            or any(
                word in path.name.lower()
                for word in ("kubeconfig", "credential", "private-key", "backup", "dump")
            )
            or (
                "secret" in path.name.lower()
                and path.suffix.lower() not in {".yaml", ".yml", ".json"}
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
        if re.search(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|client-key-data\s*:", text):
            excluded[name] = "Contains private key material."
            continue
        if path.suffix.lower() in {".yaml", ".yml", ".json"}:
            text, removed = portable_yaml(text)
            if removed:
                transformed[name] = removed
            if not text.strip():
                excluded[name] = "No portable documents remain after credential exclusions."
                continue
        if any(secret and secret in text for secret in secrets):
            excluded[name] = "Contains a known lab credential."
            continue
        included[name] = text.encode()
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
        "transformed": transformed,
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
    return {
        key: value
        for key, value in manifest.items()
        if key not in {"files", "excluded", "transformed"}
    } | {
        "file_count": len(included),
        "excluded_count": len(excluded),
        "archive": destination.name,
    }
