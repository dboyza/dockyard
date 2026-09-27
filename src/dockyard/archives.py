"""Bounded portable archives: inspect every member before writing any imported file."""

from __future__ import annotations

import io
import stat
import unicodedata
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

MAX_ARCHIVE = 64 * 1024**2
MAX_CONTENT = 128 * 1024**2
MAX_MEMBER = 16 * 1024**2
MAX_MEMBERS = 5000


def member_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or len(value) > 500
        or "\\" in value
        or ":" in value
        or "\x00" in value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or any(ord(character) < 32 for character in value)
        or path.as_posix() != value
    ):
        raise ValueError("The archive contains an unsafe or ambiguous path.")
    return value


def read_archive(body: bytes) -> dict[str, bytes]:
    if not body or len(body) > MAX_ARCHIVE:
        raise ValueError("Choose a Dockyard archive no larger than 64 MiB.")
    try:
        with ZipFile(io.BytesIO(body)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_MEMBERS:
                raise ValueError("The archive exceeds the 5,000-member limit.")
            total = 0
            seen: set[str] = set()
            files = []
            for entry in entries:
                name = member_path(entry.filename.rstrip("/") if entry.is_dir() else entry.filename)
                folded = unicodedata.normalize("NFD", name).casefold()
                if folded in seen:
                    raise ValueError("The archive contains duplicate or colliding paths.")
                seen.add(folded)
                mode = entry.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if kind not in {0, stat.S_IFREG, stat.S_IFDIR} or entry.flag_bits & 1:
                    raise ValueError(
                        "Linked, special, and encrypted archive entries are unsupported."
                    )
                if entry.is_dir():
                    if entry.file_size:
                        raise ValueError("Archive directory entries must be empty.")
                    continue
                if kind == stat.S_IFDIR:
                    raise ValueError("The archive has inconsistent directory metadata.")
                if not 0 <= entry.file_size <= MAX_MEMBER:
                    raise ValueError("An archive member exceeds the 16 MiB source-file limit.")
                total += entry.file_size
                if total > MAX_CONTENT:
                    raise ValueError("The expanded archive exceeds the 128 MiB limit.")
                files.append((name, entry))
            # Reject file/directory collisions on case-insensitive macOS filesystems,
            # including implicit parents, before a caller can extract any content.
            file_names = {unicodedata.normalize("NFD", name).casefold() for name, _ in files}
            for name, _ in files:
                for parent in PurePosixPath(name).parents:
                    if parent.as_posix() == ".":
                        continue
                    if unicodedata.normalize("NFD", parent.as_posix()).casefold() in file_names:
                        raise ValueError("The archive uses the same path as a file and directory.")
            result = {}
            for name, entry in files:
                with archive.open(entry) as source:
                    data = source.read(MAX_MEMBER + 1)
                if len(data) != entry.file_size or len(data) > MAX_MEMBER:
                    raise ValueError("An archive member has an invalid expanded size.")
                result[name] = data
            return result
    except (BadZipFile, NotImplementedError, RuntimeError, EOFError) as error:
        raise ValueError("The archive is corrupt or uses an unsupported ZIP encoding.") from error
