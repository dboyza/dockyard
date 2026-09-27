"""Untrusted portable files must be validated before any extraction or profile mutation."""

import io
import stat
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest

from dockyard.archives import read_archive


def packed(entries):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for name, body in entries:
            archive.writestr(name, body)
    return buffer.getvalue()


def test_valid_source_bytes_round_trip_without_filesystem_extraction():
    body = packed(
        [("manifest.json", b"{}"), ("source/chart/templates/api.yaml", b"kind: Deployment\n")]
    )
    assert read_archive(body) == {
        "manifest.json": b"{}",
        "source/chart/templates/api.yaml": b"kind: Deployment\n",
    }


@pytest.mark.parametrize(
    "name",
    [
        "../outside",
        "/absolute",
        "source/../outside",
        "C:/file",
        "source\\file",
        "./file",
        "source//file",
    ],
)
def test_path_escape_and_ambiguous_paths_are_rejected(name):
    with pytest.raises(ValueError, match="path"):
        read_archive(packed([(name, b"unsafe")]))


@pytest.mark.parametrize(
    "paths", [("source/A", "source/a"), ("source/é", "source/e\u0301"), ("source", "source/file")]
)
def test_macos_name_collisions_are_rejected(paths):
    with pytest.raises(ValueError, match="collid|same path"):
        read_archive(packed([(name, b"content") for name in paths]))


def test_link_and_compression_bomb_are_rejected_before_extraction(monkeypatch):
    from dockyard import archives

    entry = ZipInfo("source/link")
    entry.create_system = 3
    entry.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(ValueError, match="Linked"):
        read_archive(packed([(entry, b"../../outside")]))
    monkeypatch.setattr(archives, "MAX_MEMBER", 100)
    with pytest.raises(ValueError, match="source-file limit"):
        read_archive(packed([("large.txt", b"a" * 101)]))
    monkeypatch.setattr(archives, "MAX_CONTENT", 150)
    with pytest.raises(ValueError, match="expanded"):
        read_archive(packed([("one.txt", b"a" * 100), ("two.txt", b"b" * 100)]))
