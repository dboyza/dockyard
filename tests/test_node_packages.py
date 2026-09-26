"""Offline bundles keep pinned bytes and refuse silent prerequisite migrations."""

import hashlib
import json
import tarfile
import threading
from types import SimpleNamespace

import pytest

from dockyard.runtimes import node_packages
from dockyard.runtimes.docker import RuntimeErrorBase


def test_changed_cached_bundle_is_rebuilt_from_verified_packages(tmp_path, monkeypatch):
    payload = b"pinned test package bytes"
    source = tmp_path / "native/packages/example.deb"
    source.parent.mkdir(parents=True)
    source.write_bytes(payload)
    record = {
        "packages": {
            "example.deb": {
                "version": "1",
                "path": "native/packages/example.deb",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "url": "https://invalid.example/not-needed",
            }
        }
    }
    monkeypatch.setattr(node_packages, "manifest", lambda _: record)
    runtime = SimpleNamespace(tools=tmp_path, report=lambda _: None)
    output = node_packages.bundle(runtime, threading.Event())
    initial = output.read_bytes()
    output.write_bytes(b"changed cached archive")
    assert node_packages.bundle(runtime, threading.Event()).read_bytes() == initial
    with tarfile.open(output) as archive:
        assert archive.getnames() == ["example.deb"]
        assert archive.extractfile("example.deb").read() == payload
    assert source.read_bytes() == payload
    output.with_suffix(".json").write_text("interrupted metadata")
    assert node_packages.bundle(runtime, threading.Event()).read_bytes() == initial


def test_changed_prerequisite_profile_never_mutates_a_guest(tmp_path, monkeypatch):
    monkeypatch.setattr(node_packages, "bundle", lambda *a: tmp_path / "packages.tar")
    monkeypatch.setattr(node_packages, "manifest", lambda _: {"version": "new"})
    runtime = SimpleNamespace(
        lab=SimpleNamespace(resources={"vm_packages": json.dumps({"owned": "older-profile"})}),
        discover=lambda: [{"name": "owned"}],
        report=lambda _: pytest.fail("No guest mutation stage expected"),
    )
    with pytest.raises(RuntimeErrorBase, match="profile changed"):
        node_packages.install(runtime, threading.Event())
