import uuid

import pytest

from dockyard.models import Assessment, CheckStatus
from dockyard.store import BusyError, Store, timestamp


def assessment(revision=1, independent=True, status=CheckStatus.PASS):
    return Assessment(
        id=uuid.uuid4().hex,
        unit_id="m01-processes",
        revision=revision,
        lab_id="lab-one",
        status=status,
        started_at=timestamp(),
        finished_at=timestamp(),
        file_digest="a",
        evidence=[],
        independent=independent,
    )


def test_only_observed_success_earns_progress(tmp_path):
    store = Store(tmp_path)
    store.save_assessment(assessment(status=CheckStatus.BLOCKED))
    assert not store.progress()["m01-processes"]["practiced"]
    store.save_assessment(assessment(independent=False))
    assert store.progress()["m01-processes"]["practiced"]
    assert not store.progress()["m01-processes"]["demonstrated"]
    store.save_assessment(assessment())
    assert Store(tmp_path).progress()["m01-processes"]["demonstrated"]


def test_a_new_revision_does_not_inherit_old_mastery(tmp_path):
    store = Store(tmp_path)
    store.save_assessment(assessment())
    store.save_assessment(assessment(revision=2, independent=False))
    progress = store.progress()["m01-processes"]
    assert progress["revision"] == 2
    assert not progress["demonstrated"]
    assert len(store.attempts("m01-processes")) == 2


def test_concurrent_clients_cannot_mutate_the_same_lab(tmp_path):
    first, second = Store(tmp_path), Store(tmp_path)
    operation = first.begin_operation("lab-one", "prepare")
    with pytest.raises(BusyError):
        second.begin_operation("lab-one", "reset")
    first.update_operation(operation, "done")
    second.begin_operation("lab-one", "reset")


def test_notes_and_events_survive_reopening(tmp_path):
    store = Store(tmp_path)
    store.mark("m01-processes", "hints", 1)
    store.mark("m01-processes", "hints", 1)
    store.save_note("m01-processes", "Readiness is not liveness.")
    reopened = Store(tmp_path)
    assert reopened.note("m01-processes") == "Readiness is not liveness."
    assert reopened.progress()["m01-processes"]["hints"] == 2


def test_review_dates_follow_outcomes_without_recheck_postponement(tmp_path):
    from datetime import UTC, datetime, timedelta

    store = Store(tmp_path)
    unit = "m01-processes"
    store.save_assessment(assessment(independent=False))
    first = store.progress()[unit]["review_at"]
    assert datetime.now(UTC) + timedelta(hours=23) < datetime.fromisoformat(first)
    store.save_assessment(assessment(independent=False))
    assert store.progress()[unit]["review_at"] == first
    store.save_assessment(assessment())
    independent = store.progress()[unit]["review_at"]
    assert datetime.fromisoformat(independent) > datetime.now(UTC) + timedelta(days=6)
    store.save_assessment(assessment())
    assert store.progress()[unit]["review_at"] == independent
    for status in (CheckStatus.BLOCKED, CheckStatus.STALE):
        store.save_assessment(assessment(status=status))
        assert store.progress()[unit]["review_at"] == independent
    store.save_assessment(assessment(status=CheckStatus.FAIL))
    assert datetime.fromisoformat(store.progress()[unit]["review_at"]) <= datetime.now(UTC)
    assert store.progress()[unit]["demonstrated"] == 1
    store.save_assessment(assessment(independent=False))
    assert (
        datetime.now(UTC) + timedelta(hours=23)
        < datetime.fromisoformat(store.progress()[unit]["review_at"])
        < datetime.now(UTC) + timedelta(hours=25)
    )
