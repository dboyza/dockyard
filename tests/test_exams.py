"""Timed practice must persist deadlines and refuse misleading scores."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from dockyard.exams import weighted_score
from dockyard.models import Assessment, CheckStatus, Evidence, Exam, ExamTask, Lab, Runtime
from dockyard.service import Service
from dockyard.store import BusyError, timestamp


def prepared(tmp_path):
    service = Service(tmp_path)
    exam = Exam(
        id="practice-test",
        unit_id="m01-mission",
        title="Original task set",
        track="CKAD",
        tasks=[
            ExamTask(
                id="task-one",
                title="First behavior",
                brief="Observe the required behavior.",
                weight=70,
                criteria=["first", "second"],
                remediation=["m01-processes"],
            ),
            ExamTask(
                id="task-two",
                title="Second behavior",
                brief="Observe an independent outcome.",
                weight=30,
                criteria=["third"],
                remediation=["m01-images"],
            ),
        ],
        reference_policy="Official documentation only during the timed attempt.",
    )
    service.catalog.exams[exam.id] = exam
    lab = Lab(
        id="owned-exam",
        unit_id=exam.unit_id,
        revision=1,
        runtime=Runtime.DOCKER,
        state="ready",
        workspace=str(tmp_path / "workspace"),
        created_at=timestamp(),
        updated_at=timestamp(),
    )
    service.store.save_lab(lab)
    return service, exam, lab


def evidence(exam, lab):
    return Assessment(
        id="observed",
        unit_id=exam.unit_id,
        revision=1,
        lab_id=lab.id,
        status=CheckStatus.FAIL,
        started_at=timestamp(),
        finished_at=timestamp(),
        file_digest="digest",
        independent=True,
        evidence=[
            Evidence(
                criterion=key,
                title=key,
                status=status,
                expected="true",
                observed="true" if status == CheckStatus.PASS else "false",
                diagnostic="Inspect the actual behavior.",
                points=1,
            )
            for key, status in [
                ("first", CheckStatus.PASS),
                ("second", CheckStatus.FAIL),
                ("third", CheckStatus.PASS),
            ]
        ],
    )


def test_weighted_partial_credit_and_unavailable_environment(tmp_path):
    service, exam, lab = prepared(tmp_path)
    observed = evidence(exam, lab)
    assert weighted_score(exam, observed) == (65, {"task-one": 35, "task-two": 30})
    for status in (CheckStatus.STALE, CheckStatus.BLOCKED):
        with pytest.raises(ValueError, match="cannot receive"):
            weighted_score(exam, observed.model_copy(update={"status": status}))


def test_timer_and_flags_survive_reopening_and_expiry_does_not_reset(tmp_path):
    service, exam, lab = prepared(tmp_path)
    attempt = service.exams.start(exam.id)
    deadline = datetime.fromisoformat(attempt.deadline)
    assert timedelta(minutes=119) < deadline - datetime.now(UTC) <= timedelta(minutes=120)
    service.exams.edit(attempt.id, "task-two", ["task-one"])
    reopened = Service(tmp_path)
    reopened.catalog.exams[exam.id] = exam
    saved = reopened.exams.get(attempt.id)
    assert saved.deadline == attempt.deadline
    assert saved.selected_task == "task-two" and saved.flagged == ["task-one"]
    with pytest.raises(BusyError):
        reopened.exams.start(exam.id)
    with pytest.raises(BusyError):
        reopened.perform(exam.unit_id, "reset")
    expired = saved.model_copy(
        update={"deadline": (datetime.now(UTC) - timedelta(seconds=2)).isoformat()}
    )
    with reopened.store.connection() as connection:
        connection.execute(
            "UPDATE exams SET body=? WHERE id=?", (expired.model_dump_json(), expired.id)
        )
    reopened.exams.recover()
    recovered = reopened.exams.get(attempt.id)
    assert recovered.state == "invalidated" and recovered.score is None
    assert recovered.deadline == expired.deadline
    with pytest.raises(ValueError, match="Independent retake"):
        reopened.exams.start(exam.id)


def test_finish_scores_once_and_keeps_task_remediation_evidence(tmp_path, monkeypatch):
    service, exam, lab = prepared(tmp_path)
    attempt = service.exams.start(exam.id)
    calls = []

    def assess(unit_id, action, *, exam_submission=False):
        calls.append((unit_id, action, exam_submission))
        return evidence(exam, lab).model_dump(mode="json")

    monkeypatch.setattr(service, "perform", assess)
    finished = service.exams.finish(attempt.id)
    assert finished.state == "finished" and finished.score == 65
    assert finished.assessment_id == "observed"
    assert service.exams.finish(attempt.id) == finished
    assert calls == [(exam.unit_id, "check", True)]


def test_technical_failure_is_invalidated_without_zero_score(tmp_path, monkeypatch):
    service, exam, lab = prepared(tmp_path)
    attempt = service.exams.start(exam.id)
    observed = evidence(exam, lab).model_copy(update={"status": CheckStatus.BLOCKED})
    monkeypatch.setattr(service, "perform", lambda *a, **k: observed.model_dump(mode="json"))
    finished = service.exams.finish(attempt.id)
    assert finished.state == "invalidated" and finished.score is None
    assert "No score" in finished.reason


def test_deadline_monitor_submits_without_a_browser_and_blocks_reused_fixture(
    tmp_path, monkeypatch
):
    import threading

    service, exam, lab = prepared(tmp_path)
    attempt = service.exams.start(exam.id)
    ready = threading.Event()
    original_recover = service.exams.recover

    def recovered():
        original_recover()
        ready.set()

    monkeypatch.setattr(service.exams, "recover", recovered)
    monkeypatch.setattr(
        service, "perform", lambda *a, **k: evidence(exam, lab).model_dump(mode="json")
    )
    worker = service.exams.start_monitor()
    try:
        assert ready.wait(3)
        expired = attempt.model_copy(
            update={"deadline": (datetime.now(UTC) - timedelta(seconds=1)).isoformat()}
        )
        with service.store.connection() as connection:
            connection.execute(
                "UPDATE exams SET body=? WHERE id=?", (expired.model_dump_json(), attempt.id)
            )
        deadline = datetime.now(UTC) + timedelta(seconds=5)
        while service.exams.get(attempt.id).state != "finished" and datetime.now(UTC) < deadline:
            threading.Event().wait(0.05)
        assert service.exams.get(attempt.id).score == 65
        assert "Independent retake" in service.exams.readiness(exam.id)
    finally:
        service.shutdown()
        worker.join(3)
    assert not worker.is_alive()
