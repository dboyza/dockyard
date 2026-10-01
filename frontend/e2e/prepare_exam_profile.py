"""Prepare a disposable profile for e2e/exam.spec.ts.

Run with the installed interpreter so the profile owns its tools:
    .runtime/installed/bin/python frontend/e2e/prepare_exam_profile.py PROFILE

It prepares the CKAD release exam, applies its reference solution so a timed attempt can
score 100, and records one earlier invalidated attempt so saved history has two entries.
"""

import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from dockyard.models import ExamAttempt
from dockyard.service import Service

UNIT = "exam-ckad-a"

profile = Path(sys.argv[1]).resolve()
if profile.exists() and any(profile.iterdir()):
    raise SystemExit("Choose a new, empty profile directory; this one already has data.")
service = Service(profile)
service.perform(UNIT, "prepare")
lab = service.store.lab(UNIT)
assert lab is not None
workspace = Path(lab.workspace)
for source in (Path(service.catalog.root) / "units" / UNIT / "reference").iterdir():
    shutil.copy2(source, workspace / source.name)
subprocess.run(
    ["sh", "run.sh"], cwd=workspace, env=service.environment(lab), check=True, timeout=1200
)
earlier = ExamAttempt(
    id=uuid.uuid4().hex,
    exam_id="ckad-release",
    unit_id=UNIT,
    lab_id="an-earlier-lab",
    revision=lab.revision,
    state="invalidated",
    started_at="2026-01-01T10:00:00+00:00",
    deadline="2026-01-01T12:00:00+00:00",
    finished_at="2026-01-01T10:05:00+00:00",
    selected_task="release",
    reason="The prepared exam environment changed or became unavailable. No score was assigned.",
)
with service.store.connection() as connection:
    connection.execute(
        "INSERT INTO exams(id,body) VALUES(?,?)", (earlier.id, earlier.model_dump_json())
    )
print(f"Prepared {profile}. Run the exam suite with DOCKYARD_EXAM_PROFILE={profile}")
