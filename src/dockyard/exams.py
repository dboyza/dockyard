"""Persistent practice deadlines, original task scoring, and explicit invalidation."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from dockyard.models import Assessment, CheckStatus, Exam, ExamAttempt
from dockyard.store import BusyError, timestamp

if TYPE_CHECKING:
    from dockyard.service import Service


def weighted_score(exam: Exam, assessment: Assessment) -> tuple[float, dict[str, float]]:
    if assessment.status in {CheckStatus.BLOCKED, CheckStatus.STALE}:
        raise ValueError("Unavailable or changing environments cannot receive an exam score.")
    evidence = {entry.criterion: entry for entry in assessment.evidence}
    scores = {}
    for task in exam.tasks:
        if any(key not in evidence for key in task.criteria):
            raise ValueError("The assessment is missing required task evidence.")
        available = sum(evidence[key].points for key in task.criteria)
        earned = sum(
            evidence[key].points
            for key in task.criteria
            if evidence[key].status == CheckStatus.PASS
        )
        scores[task.id] = round(task.weight * earned / available, 2)
    return round(sum(scores.values()), 2), scores


class Exams:
    def __init__(self, service: Service):
        self.service = service
        self.store = service.store

    def all(self) -> list[ExamAttempt]:
        with self.store.connection() as connection:
            rows = connection.execute("SELECT body FROM exams ORDER BY rowid DESC").fetchall()
        return [ExamAttempt.model_validate_json(row[0]) for row in rows]

    def get(self, identity: str) -> ExamAttempt:
        with self.store.connection() as connection:
            row = connection.execute("SELECT body FROM exams WHERE id=?", (identity,)).fetchone()
        if not row:
            raise ValueError("That exam attempt does not exist.")
        return ExamAttempt.model_validate_json(row[0])

    def definition(self, identity: str) -> Exam:
        try:
            return self.service.catalog.exams[identity]
        except KeyError as error:
            raise ValueError("That original practice exam does not exist.") from error

    def readiness(self, exam_id: str) -> str | None:
        exam = self.definition(exam_id)
        unit = self.service.catalog.get(exam.unit_id)
        lab = self.store.lab(exam.unit_id)
        attempts = self.all()
        if any(a.state in {"active", "grading"} for a in attempts):
            return "Finish or abandon the active timed attempt first."
        if lab is None or lab.state != "ready" or lab.revision != unit.revision:
            return "Prepare the exam environment before starting its timer."
        if any(
            o["lab_id"] == lab.id and o["state"] in {"running", "queued", "canceling"}
            for o in self.store.operations()
        ):
            return "Wait for the current environment operation to finish."
        progress = self.store.progress().get(unit.id, {})
        if progress.get("hints") or progress.get("reference"):
            return "Use Independent retake after revealing support."
        for previous in attempts:
            if (
                previous.lab_id == lab.id
                and previous.revision == unit.revision
                and self.store.setting("exam-lab-attempt:" + previous.id, 1)
                == self.store.setting("attempt-number:" + unit.id, 1)
            ):
                return "Use Independent retake to prepare a fresh timed fixture."
        return None

    def start(self, exam_id: str) -> ExamAttempt:
        exam = self.definition(exam_id)
        unit = self.service.catalog.get(exam.unit_id)
        lab = self.store.lab(exam.unit_id)
        if lab is None or lab.state != "ready" or lab.revision != unit.revision:
            raise ValueError("Prepare the exam environment before starting its timer.")
        progress = self.store.progress().get(unit.id, {})
        if progress.get("hints") or progress.get("reference"):
            raise ValueError(
                "Use Independent retake to create a fresh attempt after revealing support."
            )
        now = datetime.now(UTC)
        attempt = ExamAttempt(
            id=uuid.uuid4().hex,
            exam_id=exam.id,
            unit_id=unit.id,
            lab_id=lab.id,
            revision=unit.revision,
            state="active",
            started_at=now.isoformat(),
            deadline=(now + timedelta(minutes=exam.minutes)).isoformat(),
            selected_task=exam.tasks[0].id,
        )
        with self.store.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if reason := self.readiness(exam_id):
                if "active timed" in reason:
                    raise BusyError(reason)
                raise ValueError(reason)
            for row in connection.execute("SELECT body FROM exams"):
                previous = ExamAttempt.model_validate_json(row[0])
                if previous.state in {"active", "grading"}:
                    raise BusyError("Finish or abandon the active timed attempt first.")
                if previous.lab_id == lab.id and previous.revision == unit.revision:
                    # A new lab attempt is required, not a fresh timer on repaired work.
                    previous_number = self.store.setting("exam-lab-attempt:" + previous.id, 1)
                    if previous_number == self.store.setting("attempt-number:" + unit.id, 1):
                        raise ValueError(
                            "Use Independent retake to reset the exam fixture "
                            "before another timed attempt."
                        )
            connection.execute(
                "INSERT INTO exams(id,body) VALUES(?,?)", (attempt.id, attempt.model_dump_json())
            )
            connection.execute(
                "INSERT INTO settings(key,value) VALUES(?,?)",
                (
                    "exam-lab-attempt:" + attempt.id,
                    json.dumps(self.store.setting("attempt-number:" + unit.id, 1)),
                ),
            )
        return attempt

    def edit(self, identity: str, selected_task: str, flagged: list[str]) -> ExamAttempt:
        with self.store.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT body FROM exams WHERE id=?", (identity,)).fetchone()
            if not row:
                raise ValueError("That exam attempt does not exist.")
            attempt = ExamAttempt.model_validate_json(row[0])
            tasks = {task.id for task in self.definition(attempt.exam_id).tasks}
            if selected_task not in tasks or not set(flagged) <= tasks:
                raise ValueError("Selection and flags must name tasks in this exam.")
            if attempt.state != "active" or datetime.now(UTC) >= datetime.fromisoformat(
                attempt.deadline
            ):
                raise ValueError("This timed attempt is no longer accepting task changes.")
            attempt.selected_task = selected_task
            attempt.flagged = sorted(set(flagged))
            connection.execute(
                "UPDATE exams SET body=? WHERE id=?", (attempt.model_dump_json(), identity)
            )
        return attempt

    def invalidate(self, identity: str, reason: str) -> ExamAttempt:
        with self.store.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT body FROM exams WHERE id=?", (identity,)).fetchone()
            if not row:
                raise ValueError("That exam attempt does not exist.")
            attempt = ExamAttempt.model_validate_json(row[0])
            if attempt.state in {"active", "grading"}:
                attempt.state = "invalidated"
                attempt.finished_at = timestamp()
                attempt.reason = reason
                attempt.score = None
                connection.execute(
                    "UPDATE exams SET body=? WHERE id=?", (attempt.model_dump_json(), identity)
                )
        return attempt

    def finish(self, identity: str, *, deadline: bool = False) -> ExamAttempt:
        with self.store.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT body FROM exams WHERE id=?", (identity,)).fetchone()
            if not row:
                raise ValueError("That exam attempt does not exist.")
            attempt = ExamAttempt.model_validate_json(row[0])
            if attempt.state != "active":
                return attempt
            now = datetime.now(UTC)
            if not deadline and now > datetime.fromisoformat(attempt.deadline) + timedelta(
                seconds=5
            ):
                raise ValueError(
                    "The deadline has elapsed. Wait for the workbench's deadline assessment."
                )
            attempt.state = "grading"
            attempt.reason = (
                "Time expired; capturing final runtime evidence."
                if deadline
                else "Submitted for final runtime assessment."
            )
            connection.execute(
                "UPDATE exams SET body=? WHERE id=?", (attempt.model_dump_json(), identity)
            )
        lab = self.store.lab(attempt.unit_id)
        if (
            lab is None
            or lab.id != attempt.lab_id
            or lab.revision != attempt.revision
            or lab.state != "ready"
        ):
            return self.invalidate(
                identity,
                "The prepared exam environment changed or became unavailable. "
                "No score was assigned.",
            )
        try:
            observed = Assessment.model_validate(
                self.service.perform(attempt.unit_id, "check", exam_submission=True)
            )
            score, tasks = weighted_score(self.definition(attempt.exam_id), observed)
        except (RuntimeError, ValueError) as error:
            return self.invalidate(
                identity,
                "The final assessment could not produce stable evidence. No score was assigned. "
                + self.service.redact(str(error), lab)[:600],
            )
        attempt.state = "finished"
        attempt.finished_at = timestamp()
        attempt.assessment_id = observed.id
        attempt.score = score
        attempt.task_scores = tasks
        attempt.reason = (
            "Original practice score from the recorded final observation. "
            "This is not an official exam result or a pass probability."
        )
        with self.store.connection() as connection:
            # Do not overwrite a simultaneous explicit abandonment or shutdown invalidation.
            row = connection.execute("SELECT body FROM exams WHERE id=?", (identity,)).fetchone()
            if row and ExamAttempt.model_validate_json(row[0]).state == "grading":
                connection.execute(
                    "UPDATE exams SET body=? WHERE id=?", (attempt.model_dump_json(), identity)
                )
        return self.get(identity)

    def guard(self, unit_id: str, action: str, *, exam_submission: bool = False) -> None:
        active = next(
            (attempt for attempt in self.all() if attempt.state in {"active", "grading"}), None
        )
        if active is None:
            return
        if (
            exam_submission
            and active.unit_id == unit_id
            and active.state == "grading"
            and action == "check"
        ):
            return
        if unit_id == active.unit_id and action not in {"terminal", "note"}:
            raise BusyError(
                "Finish or abandon the timed attempt before checking, resetting, "
                "stopping, or revealing support."
            )
        if action in {"prepare", "resume", "reset", "retake", "clean"}:
            raise BusyError(
                "Finish or abandon the timed attempt before switching practice environments."
            )

    def recover(self) -> None:
        # Browser reloads do not affect the persisted deadline. A closed launcher cannot
        # capture deadline state, so expired/interrupted attempts are invalidated at startup.
        for attempt in self.all():
            if attempt.state == "grading" or (
                attempt.state == "active"
                and datetime.now(UTC) >= datetime.fromisoformat(attempt.deadline)
            ):
                self.invalidate(
                    attempt.id,
                    "The launcher was unavailable at the deadline or during grading. "
                    "No score was assigned; start a fresh attempt.",
                )

    def monitor(self) -> None:
        self.recover()
        while not self.service.closing.wait(0.5):
            for attempt in self.all():
                if attempt.state == "active" and datetime.now(UTC) >= datetime.fromisoformat(
                    attempt.deadline
                ):
                    self.finish(attempt.id, deadline=True)

    def start_monitor(self) -> threading.Thread:
        worker = threading.Thread(target=self.monitor, name="dockyard-exam-deadlines", daemon=True)
        worker.start()
        return worker
