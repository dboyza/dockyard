"""A failed test must never orphan the practice environments its profile created."""

import json
import os
import tempfile
from pathlib import Path

import pytest
from release_profile import release

from dockyard import host
from dockyard.models import Exam, ExamTask, Lab, Runtime
from dockyard.process import run
from dockyard.service import Service
from dockyard.store import timestamp
from dockyard.workspace import write_files

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("DOCKYARD_INTEGRATION") != "1", reason="opt-in real runtimes"
    ),
]


def profile_with_a_container():
    directory = Path(tempfile.mkdtemp(prefix="dy-release-", dir=host.temporary_root()))
    service = Service(directory)
    service.perform("m00-first-container", "prepare")
    lab = service.store.lab("m00-first-container")
    unit = service.catalog.get("m00-first-container")
    write_files(Path(lab.workspace), unit.reference, overwrite=True)
    assert run(["/bin/sh", "run.sh"], cwd=lab.workspace, env=service.environment(lab)).ok
    service.perform("m00-first-container", "check")
    return directory, service, service.store.lab("m00-first-container")


def owned_containers(lab):
    listed = run(["docker", "ps", "-aq", "--filter", f"label=io.dockyard.lab={lab.id}"])
    assert listed.ok, listed.stderr
    return listed.stdout.split()


def test_release_ends_a_timed_attempt_and_removes_every_lab():
    directory, service, lab = profile_with_a_container()
    assert owned_containers(lab)
    # A failed exam test leaves an active timed attempt, which blocks lab cleanup.
    exam = Exam(
        id="release-practice",
        unit_id="m01-mission",
        title="Release practice",
        track="CKAD",
        tasks=[
            ExamTask(
                id="task",
                title="Task",
                brief="Observe the behavior.",
                weight=100,
                criteria=["only"],
                remediation=["m01-processes"],
            )
        ],
        reference_policy="None.",
    )
    service.catalog.exams[exam.id] = exam
    service.store.save_lab(
        Lab(
            id="exam-practice-lab",
            unit_id=exam.unit_id,
            revision=1,
            runtime=Runtime.DOCKER,
            state="ready",
            workspace=str(directory / "exam-workspace"),
            created_at=timestamp(),
            updated_at=timestamp(),
            resources={"docker_endpoint": service._docker_endpoint(), "port": "0"},
        )
    )
    service.exams.start(exam.id)
    with pytest.raises(Exception, match="timed attempt"):
        service.perform("m00-first-container", "clean")

    release(directory)
    assert not directory.exists()
    assert owned_containers(lab) == []


def test_release_keeps_a_profile_it_cannot_confirm_empty():
    directory, service, lab = profile_with_a_container()
    inventory = lab.resources["docker_inventory"]
    tampered = [dict(item, created="2000-01-01T00:00:00Z") for item in json.loads(inventory)]
    lab.resources["docker_inventory"] = json.dumps(tampered)
    service.store.save_lab(lab)
    try:
        with pytest.raises(RuntimeError) as kept:
            release(directory)
        assert str(directory) in str(kept.value)
        assert "lab clean --all --yes" in str(kept.value)
        assert directory.exists() and owned_containers(lab)
    finally:
        # Restore the true record so the real container is still found and removed.
        lab.resources["docker_inventory"] = inventory
        service.store.save_lab(lab)
        release(directory)
    assert owned_containers(lab) == []
