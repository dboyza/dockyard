"""Explicit source continuation and readable mission portfolios without resource transfer."""

from __future__ import annotations

import difflib
import hashlib
import io
import json
import tempfile
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Any
from zipfile import ZIP_DEFLATED, ZipFile

from dockyard.locking import operation_lock
from dockyard.progress_bundle import checkpoint_file, inspect_checkpoint
from dockyard.store import timestamp
from dockyard.workspace import atomic_write, snapshot, write_files

if TYPE_CHECKING:
    from dockyard.service import Service


def checkpoint_sources(
    service: Service, identity: str
) -> tuple[dict[str, Any], dict[str, bytes], str]:
    entry = next((item for item in service.store.checkpoints() if item["id"] == identity), None)
    if entry is None:
        raise ValueError("That saved project checkpoint does not exist.")
    body = checkpoint_file(service, entry).read_bytes()
    try:
        files = inspect_checkpoint(entry, body)
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError) as error:
        raise ValueError("The checkpoint has invalid provenance metadata.") from error
    return entry, files, hashlib.sha256(body).hexdigest()


def continuation_preview(service: Service, identity: str, target_id: str) -> dict[str, Any]:
    entry, files, digest = checkpoint_sources(service, identity)
    source = service.catalog.get(entry["unit_id"])
    target = service.catalog.get(target_id)
    if target.kind != "mission" or target.module <= source.module:
        raise ValueError("Choose a mission in a later module for this project continuation.")
    existing = service.store.lab(target_id)
    if existing is not None:
        raise ValueError(
            "This mission already has a workspace. It is preserved. "
            "Choose an unstarted later mission, or adapt checkpoint files in your terminal."
        )
    if entry["revision"] != source.revision:
        raise ValueError("Reassess this checkpoint's mission before continuing an older revision.")
    candidates = []
    for name, body in files.items():
        if not name.startswith("source/"):
            continue
        relative = name.removeprefix("source/")
        previous = body.decode()
        starter = target.starter.get(relative, "")
        candidates.append(
            {
                "path": relative,
                "relationship": "unchanged"
                if previous == starter
                else "replace"
                if relative in target.starter
                else "add",
                "diff": "".join(
                    difflib.unified_diff(
                        starter.splitlines(keepends=True),
                        previous.splitlines(keepends=True),
                        fromfile="new-mission/" + relative,
                        tofile="your-checkpoint/" + relative,
                    )
                )[:60000],
            }
        )
    return {
        "checkpoint_id": identity,
        "checkpoint_digest": digest,
        "source_title": source.title,
        "target_id": target.id,
        "target_revision": target.revision,
        "target_title": target.title,
        "supported": not entry["independent"],
        "files": candidates,
        "policy": "Start with this mission's supplied scaffold "
        "and carry only the files you select. "
        "Earlier application code may need adaptation to the later architecture. "
        "No environment is started and no old workspace is overwritten.",
    }


def continue_project(
    service: Service, identity: str, target_id: str, digest: str, revision: int, selected: list[str]
) -> dict[str, Any]:
    service.exams.guard(target_id, "prepare")
    with operation_lock(service.directory / "locks", target_id):
        preview = continuation_preview(service, identity, target_id)
        if digest != preview["checkpoint_digest"] or revision != preview["target_revision"]:
            raise ValueError(
                "The checkpoint or mission changed. Review the source comparison again."
            )
        if not selected or len(selected) != len(set(selected)):
            raise ValueError("Select at least one distinct source file to carry forward.")
        allowed = {item["path"] for item in preview["files"]}
        if not set(selected) <= allowed:
            raise ValueError("A selected file is not part of the reviewed source checkpoint.")
        _, files, _ = checkpoint_sources(service, identity)
        merged = dict(service.catalog.get(target_id).starter)
        merged.update({name: files["source/" + name].decode() for name in selected})
        folded: set[str] = set()
        for name in merged:
            normalized = unicodedata.normalize("NFD", name).casefold()
            if normalized in folded:
                raise ValueError("The selected source conflicts with a scaffold filename on macOS.")
            folded.add(normalized)
        for name in folded:
            if any(parent.as_posix() in folded for parent in Path(name).parents):
                raise ValueError("A selected source file conflicts with a scaffold directory.")
        staging_root = service.directory / "staging"
        if staging_root.is_symlink():
            raise ValueError("The staging directory is linked; preserved.")
        staging_root.mkdir(exist_ok=True, mode=0o700)
        with tempfile.TemporaryDirectory(prefix="project-", dir=staging_root) as temporary:
            staged = Path(temporary) / "workspace"
            write_files(staged, merged)
            snapshot(staged)
            # Allocate only after every source file validates; never run learner source here.
            lab = service._allocate_lab(target_id)
            workspace = Path(lab.workspace)
            if workspace.exists() or workspace.is_symlink():
                raise ValueError("An unexpected workspace occupies the new location; preserved.")
            workspace.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            staged.rename(workspace)
        provenance = {
            key: preview[key]
            for key in (
                "checkpoint_id",
                "checkpoint_digest",
                "source_title",
                "target_id",
                "target_revision",
                "supported",
            )
        }
        provenance.update(selected=selected, created_at=timestamp())
        atomic_write(
            workspace.parent / "continuation.json", json.dumps(provenance, indent=2).encode()
        )
        lab.resources["continuation_checkpoint"] = identity
        service.store.save_lab(lab)
        if preview["supported"]:
            service.store.mark(target_id, "reference", revision)
        return {"lab": service.public_lab(lab), "provenance": provenance}


def export_portfolio(service: Service) -> bytes:
    latest: dict[str, dict[str, Any]] = {}
    for entry in service.store.checkpoints():
        if entry["unit_id"] not in latest:
            latest[entry["unit_id"]] = entry
    if not latest:
        raise ValueError("Complete a mission's behavior checks before exporting a portfolio.")
    files: dict[str, bytes] = {}
    index = [
        "# Dispatch infrastructure portfolio",
        "",
        "This portfolio contains the latest saved source checkpoint for each demonstrated mission.",
        "Evidence records the observed lab behavior at that time; "
        "it is not a certification or a guarantee of present runtime health.",
        "",
        "## Mission evidence",
        "",
    ]
    for unit_id, entry in sorted(latest.items()):
        _, checkpoint, _ = checkpoint_sources(service, entry["id"])
        for name, body in checkpoint.items():
            files[f"missions/{unit_id}/{name}"] = body
        support = "independent demonstration" if entry["independent"] else "supported practice"
        index.extend(
            [
                f"### {entry['title']}",
                "",
                f"Revision {entry['revision']}; {support}; observed {entry['created_at']}.",
                f"[Source and provenance](missions/{unit_id}/manifest.json) | "
                f"[Runtime evidence](missions/{unit_id}/evidence.json) | "
                f"[Observations](missions/{unit_id}/observations.md)",
                "",
            ]
        )
    index.extend(
        [
            "## Reusing this work",
            "",
            "Source directories contain Dockerfiles, manifests, charts, scripts, "
            "and runbooks that were present at the checkpoint.",
            "Read each manifest's exclusions and transformations before reuse.",
            "Regenerate credentials, adapt names and environment-specific settings, "
            "and validate against a fresh owned lab.",
            "Database backups, private keys, kubeconfigs, runtime disks, "
            "and image caches are not part of this portfolio.",
            "",
        ]
    )
    files["README.md"] = "\n".join(index).encode()
    manifest = {
        "format": "dockyard-portfolio",
        "version": 1,
        "created_at": timestamp(),
        "missions": len(latest),
        "files": {name: hashlib.sha256(body).hexdigest() for name, body in files.items()},
    }
    result = io.BytesIO()
    with ZipFile(result, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        for name, body in files.items():
            archive.writestr(name, body)
    return result.getvalue()
