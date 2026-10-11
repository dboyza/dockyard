"""Guest tool bundles carry only mapped files from verified archives, at safe guest paths."""

import hashlib
import io
import tarfile
import threading
from types import SimpleNamespace

import pytest

from dockyard import host
from dockyard.runtimes import guest_tools
from dockyard.runtimes.docker import RuntimeErrorBase


def archive(path, members):
    with tarfile.open(path, "w:gz") as output:
        for name, data, mode in members:
            info = tarfile.TarInfo(name)
            if data is None:
                info.type = tarfile.DIRTYPE
                info.mode = mode
                output.addfile(info)
                continue
            info.size = len(data)
            info.mode = mode
            output.addfile(info, io.BytesIO(data))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(monkeypatch, tmp_path, members, root="tool-1/"):
    source = tmp_path / "native/guest-tools/tool-1.tar.gz"
    source.parent.mkdir(parents=True)
    checksum = archive(source, members)
    tool = {
        "version": "1",
        "map": {"bin/tool": "usr/local/bin/tool", "rules/": "etc/tool/"},
        "archives": {
            host.architecture(): {
                "url": "https://invalid.example/tool-1.tar.gz",
                "sha256": checksum,
                "size": source.stat().st_size,
                "root": root,
            }
        },
    }
    monkeypatch.setattr(guest_tools, "MANIFEST", {"tool": tool})
    return SimpleNamespace(tools=tmp_path, report=lambda _: None)


def test_bundle_maps_only_declared_files_with_normalized_modes(tmp_path, monkeypatch):
    runtime = pin(
        monkeypatch,
        tmp_path,
        [
            ("tool-1/bin/tool", b"binary", 0o775),
            ("tool-1/rules/default.yaml", b"rule", 0o664),
            ("tool-1/docs/README", b"not needed", 0o644),
        ],
    )
    output = guest_tools.bundle(runtime, ["tool"], threading.Event())
    with tarfile.open(output) as bundled:
        members = {member.name: member for member in bundled.getmembers()}
        assert set(members) == {"usr/local/bin/tool", "etc/tool/default.yaml"}
        assert members["usr/local/bin/tool"].mode == 0o755
        assert members["etc/tool/default.yaml"].mode == 0o644
        assert {member.uid for member in members.values()} == {0}
        assert bundled.extractfile("etc/tool/default.yaml").read() == b"rule"
    # A cached bundle with matching metadata is reused byte for byte.
    assert guest_tools.bundle(runtime, ["tool"], threading.Event()).read_bytes() == (
        output.read_bytes()
    )


def test_bundle_keeps_empty_folders_inside_mapped_directories(tmp_path, monkeypatch):
    runtime = pin(
        monkeypatch,
        tmp_path,
        [
            ("tool-1/rules/", None, 0o775),
            ("tool-1/rules/rules.d/", None, 0o700),
            ("tool-1/docs/", None, 0o755),
        ],
    )
    output = guest_tools.bundle(runtime, ["tool"], threading.Event())
    with tarfile.open(output) as bundled:
        members = {member.name: member for member in bundled.getmembers()}
    # Folders inside a mapped directory are carried; unmapped ones and the mapping root are not.
    assert set(members) == {"etc/tool/rules.d"}
    assert members["etc/tool/rules.d"].isdir()
    assert members["etc/tool/rules.d"].mode == 0o755


def test_bundle_refuses_paths_that_escape_the_mapped_directory(tmp_path, monkeypatch):
    runtime = pin(monkeypatch, tmp_path, [("tool-1/rules/../../../etc/shadow", b"x", 0o644)])
    with pytest.raises(RuntimeErrorBase, match="unsafe path"):
        guest_tools.bundle(runtime, ["tool"], threading.Event())


def test_pinned_manifest_covers_both_architectures():
    for name, tool in guest_tools.MANIFEST.items():
        assert set(tool["archives"]) == {"arm64", "amd64"}, name
        for entry in tool["archives"].values():
            assert len(entry["sha256"]) == 64 and entry["url"].startswith("https://")
        assert all(not target.startswith("/") for target in tool["map"].values())
