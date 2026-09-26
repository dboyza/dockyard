"""Real learner files with bounded snapshots and reversible resets."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path, PurePosixPath

EXCLUDED = {".git", ".venv", "node_modules", "__pycache__", ".DS_Store"}
MAX_FILES = 2000
MAX_BYTES = 16 * 1024 * 1024


class WorkspaceError(ValueError):
    pass


def safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise WorkspaceError("Workspace paths must stay inside the lab directory.")
    if any(part in EXCLUDED for part in path.parts):
        raise WorkspaceError("This path is reserved for local tooling.")
    return path


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        parent = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_files(directory: Path, files: dict[str, str], *, overwrite: bool = False) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    root = directory.resolve()
    # Validate the entire manifest before writing anything.
    destinations: list[tuple[Path, str]] = []
    for name, content in files.items():
        path = directory.joinpath(*safe_relative(name).parts)
        if not path.resolve().is_relative_to(root):
            raise WorkspaceError("A workspace link points outside the lab.")
        if path.is_symlink():
            raise WorkspaceError("Refusing to overwrite a symbolic link.")
        if path.exists() and not overwrite:
            raise WorkspaceError(f"Preserving the existing file: {name}")
        destinations.append((path, content))
    for path, content in destinations:
        atomic_write(path, content.encode())


def snapshot(directory: Path) -> tuple[str, dict[str, bytes]]:
    files: dict[str, bytes] = {}
    total = 0
    root = directory.resolve()
    for current, directories, names in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in EXCLUDED)
        for name in directories:
            if (Path(current) / name).is_symlink():
                raise WorkspaceError("Remove directory symlinks before checking or exporting.")
        for name in sorted(names):
            if name in EXCLUDED:
                continue
            path = Path(current) / name
            if path.is_symlink() or not path.is_file():
                raise WorkspaceError("Only regular files can be checked or exported.")
            size = path.stat().st_size
            if total + size > MAX_BYTES or len(files) >= MAX_FILES:
                raise WorkspaceError("The lab exceeds the 16 MiB / 2,000 source-file limit.")
            with path.open("rb") as source:
                body = source.read(MAX_BYTES - total + 1)
            total += len(body)
            if total > MAX_BYTES:
                raise WorkspaceError("The workspace changed beyond the snapshot limit.")
            files[path.relative_to(root).as_posix()] = body
    digest = hashlib.sha256()
    for name, body in sorted(files.items()):
        digest.update(json.dumps([name, len(body)]).encode())
        digest.update(body)
    return digest.hexdigest(), files


def reset(directory: Path, starter: dict[str, str], backups: Path) -> Path:
    """Stage replacement first, then preserve the complete old workspace by rename."""
    if directory.is_symlink():
        raise WorkspaceError("Refusing to reset a linked workspace.")
    staged = directory.with_name(f".{directory.name}-new-{uuid.uuid4().hex}")
    try:
        write_files(staged, starter)
        backups.mkdir(parents=True, exist_ok=True)
        backup = backups / f"{directory.name}-{uuid.uuid4().hex}"
        if directory.exists():
            directory.rename(backup)
        try:
            staged.rename(directory)
        except OSError:
            if backup.exists() and not directory.exists():
                backup.rename(directory)
            raise
        return backup
    finally:
        if staged.exists():
            shutil.rmtree(staged)
