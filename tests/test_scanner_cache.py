"""Pinned scanner data must be verified before an offline exercise trusts it."""

import hashlib
import json

import pytest

from dockyard.runtimes import scanner
from dockyard.runtimes.docker import RuntimeErrorBase


def test_scanner_cache_checks_bytes_schema_and_publication_time(tmp_path, monkeypatch):
    payload = b"small database stand-in"
    expected = {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "schema": 2,
        "updated_at": "2026-09-26T12:00:00Z",
    }
    monkeypatch.setitem(scanner.SCANNER, "database", expected)
    root = tmp_path / "cache"
    database = root / "db"
    database.mkdir(parents=True)
    assert not scanner.ready(root)
    (database / "trivy.db").write_bytes(payload)
    metadata = database / "metadata.json"
    record = {"Version": 2, "UpdatedAt": expected["updated_at"], "DownloadedAt": "arbitrary"}
    metadata.write_text(json.dumps(record))
    assert scanner.ready(root)
    record["UpdatedAt"] = "a different database snapshot"
    metadata.write_text(json.dumps(record))
    assert not scanner.ready(root)
    record["UpdatedAt"] = expected["updated_at"]
    metadata.write_text(json.dumps(record))
    (database / "trivy.db").write_bytes(payload + b"changed")
    assert not scanner.ready(root)


def test_scanner_cache_rejects_external_link_without_reading_it(tmp_path):
    external = tmp_path / "external"
    external.mkdir()
    (external / "keep").write_text("preserve")
    cache = tmp_path / "cache"
    cache.symlink_to(external, target_is_directory=True)
    with pytest.raises(RuntimeErrorBase, match="symbolic link"):
        scanner.ready(cache)
    assert (external / "keep").read_text() == "preserve"
