"""Perform a real terminal-side learner repair in the disposable browser test profile."""

import sys
import time
from pathlib import Path

from dockyard.process import run
from dockyard.service import Service
from dockyard.workspace import write_files

service = Service(Path(sys.argv[1]))
unit = service.catalog.get(sys.argv[2])
lab = service.store.lab(unit.id)
assert lab is not None
workspace = Path(lab.workspace)
write_files(workspace, unit.reference, overwrite=True)
result = run(["/bin/sh", "run.sh"], cwd=workspace, env=service.environment(lab), timeout=120)
assert result.ok, result.stdout + result.stderr
# The assessment discovers and records the resources created in the learner terminal.
deadline = time.monotonic() + 20
while True:
    assessment = service.perform(unit.id, "check")
    if assessment["status"] == "pass" or time.monotonic() >= deadline:
        break
    time.sleep(0.25)
assert assessment["status"] == "pass", assessment
