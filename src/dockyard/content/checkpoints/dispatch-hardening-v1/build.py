"""Build the authored source using the already verified local teaching fixture."""

import json
import os
import subprocess
from pathlib import Path

config = json.loads(Path("build.json").read_text())
legacy = config["include_legacy_dependency"]
if not isinstance(legacy, bool):
    raise SystemExit("include_legacy_dependency must be a JSON boolean.")
subprocess.run(
    [
        "docker",
        "build",
        "--build-arg",
        "BASE_IMAGE=" + os.environ["DOCKYARD_PYTHON_IMAGE"],
        "--build-arg",
        "INCLUDE_LEGACY=" + str(legacy).lower(),
        "--build-context",
        "fixture=" + str(Path(os.environ["DOCKYARD_STORAGE"]) / "packages"),
        "--label",
        "io.dockyard.lab=" + os.environ["DOCKYARD_LAB"],
        "-t",
        os.environ["DOCKYARD_IMAGE"],
        ".",
    ],
    check=True,
    timeout=300,
)
subprocess.run(
    [
        "kind",
        "load",
        "docker-image",
        os.environ["DOCKYARD_IMAGE"],
        "--name",
        os.environ["DOCKYARD_CLUSTER"],
    ],
    check=True,
    timeout=180,
)
