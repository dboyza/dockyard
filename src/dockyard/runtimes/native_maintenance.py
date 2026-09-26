"""Stage pinned maintenance inputs without performing the learner's upgrade."""

from __future__ import annotations

import threading

from dockyard.runtimes.linux import LinuxRuntime
from dockyard.runtimes.node_packages import bundle


def stage_upgrade(runtime: LinuxRuntime, cancel: threading.Event) -> str:
    archive = bundle(runtime, cancel, "1.35.8")
    directory = "/tmp/dockyard-" + runtime.lab.id + "-upgrade"
    for entry in runtime.discover():
        name = entry["name"]
        runtime.require(runtime.guest(name, ["mkdir", "-p", "-m", "700", directory], cancel=cancel))
        runtime.copy_to(name, archive, directory + "/packages.tar", cancel=cancel)
        runtime.require(
            runtime.guest(
                name,
                ["tar", "--no-same-owner", "-xf", directory + "/packages.tar", "-C", directory],
                timeout=60,
                cancel=cancel,
            )
        )
    return directory
