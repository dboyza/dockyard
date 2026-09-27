"""Build the supplied Dispatch application and transfer its native image."""

import os
import subprocess
import sys

subprocess.run(
    [
        "docker",
        "build",
        "--build-arg",
        "BASE_IMAGE=" + os.environ["DOCKYARD_PYTHON_IMAGE"],
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
    [sys.executable, "-m", "dockyard.native", "load-image", os.environ["DOCKYARD_IMAGE"]],
    check=True,
    timeout=420,
)
