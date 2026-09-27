"""Portable progress and source drafts, kept separate from live resource ownership."""

from __future__ import annotations

import hashlib
import io
import json
import re
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import Field, model_validator

from dockyard.archives import MAX_ARCHIVE, member_path, read_archive
from dockyard.locking import operation_lock
from dockyard.models import Assessment, Contract, ExamAttempt, Identifier
from dockyard.portfolio import portable_sources, redact_observations
from dockyard.store import BusyError, timestamp
from dockyard.workspace import atomic_write, snapshot

if TYPE_CHECKING:
    from dockyard.service import Service


class ProgressRow(Contract):
    unit_id: Identifier
    viewed: int = Field(ge=0, le=1)
    practiced: int = Field(ge=0, le=1)
    demonstrated: int = Field(ge=0, le=1)
    hints: int = Field(ge=0, le=100000)
    reference: int = Field(ge=0, le=1)
    revision: int = Field(ge=0)
    review_at: str | None
    updated_at: str


class SavedNote(Contract):
    body: str = Field(max_length=100000)
    updated_at: str


class CheckpointRecord(Contract):
    format: Literal["dockyard-checkpoint"]
    version: Literal[1]
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    unit_id: Identifier
    revision: int = Field(ge=1)
    title: str = Field(max_length=500)
    created_at: str
    lab_id: str = Field(max_length=200)
    independent: bool
    hints_used: int = Field(ge=0)
    reference_revealed: bool
    file_count: int = Field(ge=0, le=5000)
    excluded_count: int = Field(ge=0, le=5000)
    archive: str = Field(pattern=r"^[a-f0-9]{32}\.zip$")


class Records(Contract):
    format: Literal["dockyard-progress"] = "dockyard-progress"
    version: Literal[1] = 1
    created_at: str
    progress: list[ProgressRow] = Field(max_length=5000)
    notes: dict[Identifier, SavedNote]
    attempts: list[Assessment] = Field(max_length=10000)
    exams: list[ExamAttempt] = Field(max_length=1000)
    checkpoints: list[dict[str, Any]] = Field(max_length=1000)
    theme: Literal["dark", "light"] = "dark"
    last_unit: Identifier | None = None
    exclusions: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_records(self) -> Records:
        dates = [self.created_at]
        for entry in self.progress:
            dates.extend([entry.updated_at, *([entry.review_at] if entry.review_at else [])])
        dates.extend(note.updated_at for note in self.notes.values())
        dates.extend(date for a in self.attempts for date in (a.started_at, a.finished_at))
        dates.extend(date for a in self.exams for date in (a.started_at, a.deadline))
        dates.extend(a.finished_at for a in self.exams if a.finished_at)
        for checkpoint in self.checkpoints:
            saved = CheckpointRecord.model_validate(checkpoint)
            dates.append(saved.created_at)
        for date in dates:
            if datetime.fromisoformat(date).tzinfo is None:
                raise ValueError("Portable evidence dates must include a timezone.")
        for identities in (
            [row.unit_id for row in self.progress],
            [row.id for row in self.attempts],
            [row.id for row in self.exams],
            [row["id"] for row in self.checkpoints],
        ):
            if len(identities) != len(set(identities)):
                raise ValueError("The archive contains duplicate record identities.")
        return self


def checkpoint_file(service: Service, entry: dict[str, Any]) -> Path:
    name = str(entry.get("archive", ""))
    if not re.fullmatch(r"[a-f0-9]{32}\.zip", name):
        raise ValueError("A checkpoint has an invalid archive identity.")
    root = service.directory / "checkpoints"
    target = root / name
    if (
        root.is_symlink()
        or target.is_symlink()
        or not target.resolve().is_relative_to(root.resolve())
    ):
        raise ValueError("A checkpoint archive points outside its owned directory.")
    if not target.is_file() or target.stat().st_size > MAX_ARCHIVE:
        raise ValueError("A checkpoint archive is missing or exceeds the portable size limit.")
    return target


def export_bundle(service: Service) -> bytes:
    with operation_lock(service.directory / "locks", "progress-transfer"):
        secrets = [
            value
            for lab in service.store.labs()
            for key, value in lab.resources.items()
            if key in {"db_password", "bootstrap_token"}
        ]
        files: dict[str, bytes] = {}
        exclusions: dict[str, str] = {}
        for lab in service.store.labs():
            workspace = Path(lab.workspace)
            if not workspace.exists():
                continue
            if workspace.is_symlink() or not workspace.resolve().is_relative_to(service.directory):
                raise ValueError("A draft workspace is outside this profile's owned directory.")
            _, draft = snapshot(workspace)
            kept, omitted, transformed = portable_sources(draft, secrets)
            for name, body in kept.items():
                files[f"drafts/{lab.unit_id}/{name}"] = body
            exclusions.update({f"{lab.unit_id}/{name}": reason for name, reason in omitted.items()})
            exclusions.update(
                {
                    f"{lab.unit_id}/{name}": "; ".join(reasons)
                    for name, reasons in transformed.items()
                }
            )
        with service.store.connection() as connection:
            # One SQLite read transaction provides a consistent learning-record snapshot.
            connection.execute("BEGIN")
            progress = [
                ProgressRow.model_validate(dict(row))
                for row in connection.execute("SELECT * FROM progress")
            ]
            notes = {
                row["unit_id"]: SavedNote(
                    body=redact_observations(row["body"], secrets), updated_at=row["updated_at"]
                )
                for row in connection.execute("SELECT * FROM notes")
            }
            attempts = [
                Assessment.model_validate_json(redact_observations(row[0], secrets))
                for row in connection.execute("SELECT body FROM attempts")
            ]
            exams = [
                ExamAttempt.model_validate_json(redact_observations(row[0], secrets))
                for row in connection.execute("SELECT body FROM exams")
            ]
            checkpoints = [
                json.loads(row[0]) for row in connection.execute("SELECT body FROM checkpoints")
            ]
        for entry in checkpoints:
            files["checkpoints/" + entry["archive"]] = checkpoint_file(service, entry).read_bytes()
        records = Records(
            created_at=timestamp(),
            progress=progress,
            notes=notes,
            attempts=attempts,
            exams=exams,
            checkpoints=checkpoints,
            exclusions=exclusions,
            theme=service.store.setting("theme", "dark"),
            last_unit=service.store.setting("last_unit"),
        )
        files["records.json"] = records.model_dump_json(indent=2).encode()
        manifest = {
            "format": "dockyard-progress-bundle",
            "version": 1,
            "files": {
                member_path(name): hashlib.sha256(body).hexdigest() for name, body in files.items()
            },
        }
        buffer = io.BytesIO()
        with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2))
            for name, body in files.items():
                archive.writestr(name, body)
        body = buffer.getvalue()
        read_archive(body)
        return body


def inspect_checkpoint(entry: dict[str, Any], body: bytes) -> dict[str, bytes]:
    CheckpointRecord.model_validate(entry)
    nested = read_archive(body)
    proof = json.loads(nested["manifest.json"])
    evidence = Assessment.model_validate_json(nested["evidence.json"])
    if (
        proof.get("format") != "dockyard-checkpoint"
        or proof.get("version") != 1
        or proof["id"] != entry["id"]
        or proof["unit_id"] != entry["unit_id"]
        or evidence.unit_id != entry["unit_id"]
        or evidence.revision != entry["revision"]
        or evidence.lab_id != entry["lab_id"]
        or evidence.finished_at != entry["created_at"]
        or any(
            proof.get(key) != value
            for key, value in entry.items()
            if key not in {"archive", "file_count", "excluded_count"}
        )
        or len(proof["files"]) != entry["file_count"]
        or len(proof["excluded"]) != entry["excluded_count"]
    ):
        raise ValueError("Checkpoint provenance does not match its inventory.")
    if proof["files"] != {
        k.removeprefix("source/"): hashlib.sha256(v).hexdigest()
        for k, v in nested.items()
        if k.startswith("source/")
    }:
        raise ValueError("A checkpoint source file failed its integrity check.")
    if set(nested) != {"manifest.json", "evidence.json", "observations.md"} | {
        "source/" + member_path(k) for k in proof["files"]
    }:
        raise ValueError("A checkpoint contains undeclared files.")
    return nested


def inspect_bundle(service: Service, body: bytes) -> tuple[Records, dict[str, bytes]]:
    files = read_archive(body)
    try:
        manifest = json.loads(files.pop("manifest.json"))
        if manifest.get("format") != "dockyard-progress-bundle" or manifest.get("version") != 1:
            raise ValueError("This file is not a supported Dockyard progress bundle.")
        hashes = manifest["files"]
        if hashes != {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}:
            raise ValueError("The archive contents do not match their integrity manifest.")
        records = Records.model_validate_json(files["records.json"])
        known = service.catalog.units
        identities = {p.unit_id for p in records.progress} | set(records.notes)
        identities |= {a.unit_id for a in records.attempts} | {a.unit_id for a in records.exams}
        if not identities <= known.keys():
            raise ValueError(
                "This archive references curriculum units unavailable in this version."
            )
        revisions = [(p.unit_id, p.revision) for p in records.progress]
        revisions += [(a.unit_id, a.revision) for a in records.attempts]
        revisions += [(e.unit_id, e.revision) for e in records.exams]
        for unit_id, revision in revisions:
            if revision > known[unit_id].revision:
                raise ValueError("This archive needs a newer curriculum revision.")
        if records.last_unit is not None and records.last_unit not in known:
            raise ValueError("The saved resume location names an unavailable unit.")
        assessments = {a.id: a for a in records.attempts}
        for exam in records.exams:
            definition = service.catalog.exams.get(exam.exam_id)
            if definition is None or definition.unit_id != exam.unit_id:
                raise ValueError("An exam record does not match its curriculum definition.")
            tasks = {task.id for task in definition.tasks}
            if exam.selected_task not in tasks or not set(exam.flagged) <= tasks:
                raise ValueError("An exam record refers to unknown tasks.")
            if exam.state == "finished":
                assessment = assessments.get(exam.assessment_id or "")
                if assessment is None or (
                    assessment.unit_id,
                    assessment.revision,
                    assessment.lab_id,
                ) != (exam.unit_id, exam.revision, exam.lab_id):
                    raise ValueError("A finished exam is missing its matching runtime evidence.")
                if exam.revision == known[exam.unit_id].revision:
                    from dockyard.exams import weighted_score

                    score, scores = weighted_score(definition, assessment)
                    if exam.score != score or exam.task_scores != scores:
                        raise ValueError("An exam score does not match its recorded evidence.")
        expected = {"records.json"}
        for name in files:
            if name.startswith("drafts/"):
                parts = name.split("/", 2)
                if len(parts) != 3 or parts[1] not in known:
                    raise ValueError("A source draft names an unavailable unit.")
                expected.add(name)
        for entry in records.checkpoints:
            identity = str(entry["id"])
            if not re.fullmatch(r"[a-f0-9]{32}", identity) or entry["archive"] != identity + ".zip":
                raise ValueError("The checkpoint inventory has an invalid identity.")
            if (
                entry["unit_id"] not in known
                or entry["revision"] > known[entry["unit_id"]].revision
            ):
                raise ValueError("A checkpoint needs a different curriculum version.")
            name = "checkpoints/" + entry["archive"]
            inspect_checkpoint(entry, files[name])
            expected.add(name)
        if set(files) != expected:
            raise ValueError("The bundle contains undeclared files.")
        return records, files
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("The progress bundle is incomplete or has invalid metadata.") from error


def preview_import(service: Service, body: bytes) -> dict[str, Any]:
    records, files = inspect_bundle(service, body)
    current = service.store.progress()
    note_conflicts = sum(
        bool(service.store.note(unit) and service.store.note(unit) != note.body)
        for unit, note in records.notes.items()
    )
    return {
        "digest": hashlib.sha256(body).hexdigest(),
        "created_at": records.created_at,
        "progress_units": len(records.progress),
        "new_progress_units": sum(row.unit_id not in current for row in records.progress),
        "assessments": len(records.attempts),
        "exams": len(records.exams),
        "checkpoints": len(records.checkpoints),
        "draft_files": sum(name.startswith("drafts/") for name in files),
        "notes": len(records.notes),
        "preserved_local_notes": note_conflicts,
        "older_revisions": sum(
            row.revision < service.catalog.get(row.unit_id).revision for row in records.progress
        ),
        "policy": "Merge historical evidence. Keep existing notes and active workspaces. "
        "Imported drafts and conflicting notes are saved in a separate import folder. "
        "No containers, clusters, credentials, or live resource ownership are restored.",
    }


def import_bundle(service: Service, body: bytes, expected_digest: str) -> dict[str, Any]:
    import sqlite3

    if hashlib.sha256(body).hexdigest() != expected_digest:
        raise ValueError("The selected archive changed after its preview. Review it again.")
    with operation_lock(service.directory / "locks", "progress-transfer"):
        records, files = inspect_bundle(service, body)
        if any(
            o["state"] in {"running", "queued", "canceling"} for o in service.store.operations()
        ):
            raise BusyError("Finish active lab operations before importing progress.")
        if any(a.state in {"active", "grading"} for a in service.exams.all()):
            raise BusyError("Finish or abandon the active exam before importing progress.")
        receipt_key = "progress-import:" + expected_digest
        if previous := service.store.setting(receipt_key):
            return dict(previous) | {"already_imported": True}
        summary = preview_import(service, body)
        imported = service.directory / "imports"
        checkpoints = service.directory / "checkpoints"
        backups = service.directory / "backups"
        for root in (imported, checkpoints, backups):
            if root.is_symlink():
                raise ValueError("An import destination is a symbolic link; preserved.")
            root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for entry in records.checkpoints:
            destination = checkpoints / entry["archive"]
            if (destination.exists() or destination.is_symlink()) and (
                destination.is_symlink()
                or not destination.is_file()
                or destination.read_bytes() != files["checkpoints/" + entry["archive"]]
            ):
                raise ValueError("A checkpoint identity conflicts with a local archive; preserved.")
        identity = uuid.uuid4().hex
        destination = imported / identity
        with tempfile.TemporaryDirectory(prefix=".staging-", dir=imported) as temporary:
            staging = Path(temporary)
            for name, data in files.items():
                atomic_write(staging / name, data)
            for unit_id, note in records.notes.items():
                atomic_write(staging / "notes" / (unit_id + ".md"), note.body.encode())
            atomic_write(
                staging / "IMPORT.md",
                (
                    b"# Imported personal learning history\n\n"
                    b"These files are historical source drafts and evidence, not a running lab.\n"
                    b"Your existing workspaces and notes have been preserved.\n"
                    b"Use a fresh owned lab before checking imported work.\n"
                ),
            )
            with service.store.connection() as connection:
                backup = backups / ("progress-before-import-" + identity + ".sqlite3")
                with sqlite3.connect(backup) as target:
                    connection.backup(target)
                backup.chmod(0o600)
                connection.execute("BEGIN IMMEDIATE")
                for row in records.progress:
                    previous = connection.execute(
                        "SELECT * FROM progress WHERE unit_id=?", (row.unit_id,)
                    ).fetchone()
                    incoming = row.model_dump()
                    if previous:
                        existing = dict(previous)
                        if existing["revision"] > row.revision:
                            incoming = existing
                        elif existing["revision"] == row.revision:
                            incoming = {
                                **incoming,
                                **{
                                    key: max(incoming[key], existing[key])
                                    for key in (
                                        "viewed",
                                        "practiced",
                                        "demonstrated",
                                        "hints",
                                        "reference",
                                    )
                                },
                            }
                            dates = [d for d in (existing["review_at"], row.review_at) if d]
                            incoming["review_at"] = (
                                min(dates, key=datetime.fromisoformat) if dates else None
                            )
                        incoming["viewed"] = max(row.viewed, existing["viewed"])
                    incoming["updated_at"] = timestamp()
                    connection.execute(
                        "INSERT INTO progress(unit_id,viewed,practiced,demonstrated,hints,"
                        "reference,revision,review_at,updated_at) "
                        "VALUES(:unit_id,:viewed,:practiced,:demonstrated,:hints,:reference,"
                        ":revision,:review_at,:updated_at) "
                        "ON CONFLICT(unit_id) DO UPDATE SET viewed=excluded.viewed,"
                        "practiced=excluded.practiced,"
                        "demonstrated=excluded.demonstrated,hints=excluded.hints,reference=excluded.reference,"
                        "revision=excluded.revision,review_at=excluded.review_at,updated_at=excluded.updated_at",
                        incoming,
                    )
                for unit_id, note in records.notes.items():
                    connection.execute(
                        "INSERT OR IGNORE INTO notes(unit_id,body,updated_at) VALUES(?,?,?)",
                        (unit_id, note.body, note.updated_at),
                    )
                for assessment in records.attempts:
                    connection.execute(
                        "INSERT OR IGNORE INTO attempts(id,unit_id,created_at,body) "
                        "VALUES(?,?,?,?)",
                        (
                            assessment.id,
                            assessment.unit_id,
                            assessment.finished_at,
                            assessment.model_dump_json(),
                        ),
                    )
                for exam in records.exams:
                    if exam.state in {"active", "grading"}:
                        exam = exam.model_copy(
                            update={
                                "state": "invalidated",
                                "score": None,
                                "task_scores": {},
                                "assessment_id": None,
                                "finished_at": timestamp(),
                                "reason": (
                                    "Imported while unfinished. Its runtime and deadline "
                                    "were not restored; no score was assigned."
                                ),
                            }
                        )
                    connection.execute(
                        "INSERT OR IGNORE INTO exams(id,body) VALUES(?,?)",
                        (exam.id, exam.model_dump_json()),
                    )
                for entry in records.checkpoints:
                    target = checkpoints / entry["archive"]
                    if not target.exists():
                        atomic_write(target, files["checkpoints/" + entry["archive"]])
                    connection.execute(
                        "INSERT OR IGNORE INTO checkpoints(id,unit_id,created_at,body) "
                        "VALUES(?,?,?,?)",
                        (entry["id"], entry["unit_id"], entry["created_at"], json.dumps(entry)),
                    )
                if not connection.execute("SELECT 1 FROM settings WHERE key='theme'").fetchone():
                    connection.execute(
                        "INSERT INTO settings(key,value) VALUES('theme',?)",
                        (json.dumps(records.theme),),
                    )
                receipt = summary | {
                    "id": identity,
                    "imported_at": timestamp(),
                    "directory": str(destination),
                    "backup": str(backup),
                    "already_imported": False,
                }
                staging.rename(destination)
                connection.execute(
                    "INSERT INTO settings(key,value) VALUES(?,?)",
                    (receipt_key, json.dumps(receipt)),
                )
                connection.execute(
                    "INSERT OR IGNORE INTO settings(key,value) VALUES('last_unit',?)",
                    (json.dumps(records.last_unit),),
                )
        return receipt


def stage_import(service: Service, body: bytes) -> dict[str, Any]:
    summary = preview_import(service, body)
    root = service.directory / "imports"
    if root.is_symlink():
        raise ValueError("The import directory is linked; preserved.")
    with operation_lock(service.directory / "locks", "progress-transfer"):
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = root / "pending.zip"
        if path.is_symlink() or (path.exists() and not service.store.setting("pending-import")):
            raise ValueError("An unrecorded file occupies the import preview path; preserved.")
        atomic_write(path, body)
        service.store.set_setting("pending-import", summary["digest"])
    return summary


def import_staged(service: Service, digest: str) -> dict[str, Any]:
    if not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("Choose and preview a progress archive first.")
    if previous := service.store.setting("progress-import:" + digest):
        return dict(previous) | {"already_imported": True}
    path = service.directory / "imports/pending.zip"
    if service.store.setting("pending-import") != digest or path.is_symlink() or not path.is_file():
        raise ValueError(
            "This preview was replaced or removed. Select and review the archive again."
        )
    if path.stat().st_size > MAX_ARCHIVE:
        raise ValueError("The pending archive exceeds the portable size limit.")
    receipt = import_bundle(service, path.read_bytes(), digest)
    with operation_lock(service.directory / "locks", "progress-transfer"):
        if service.store.setting("pending-import") == digest:
            path.unlink(missing_ok=True)
            service.store.set_setting("pending-import", None)
    return receipt


def save_export(body: bytes, destination: Path) -> None:
    """Publish a complete archive without overwriting a pre-existing destination."""
    import os

    if destination.exists() or destination.is_symlink():
        raise ValueError("That export destination already exists. Choose a new filename.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=".dockyard-export-", dir=destination.parent
    ) as temporary:
        temporary.write(body)
        temporary.flush()
        os.fsync(temporary.fileno())
        try:
            os.link(temporary.name, destination)
        except FileExistsError as error:
            raise ValueError(
                "The export destination appeared during export; it was preserved."
            ) from error
