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


def wait_node(runtime: LinuxRuntime, name: str, cancel: threading.Event) -> None:
    """Require live target-version readiness and settled static processes before the next node."""
    import json
    import time
    from contextlib import suppress

    from dockyard.runtimes.docker import RuntimeErrorBase

    names = [entry["name"] for entry in runtime.discover()]
    if name not in names:
        raise RuntimeErrorBase("Maintenance observation must target a recorded guest.")
    deadline = time.monotonic() + 180
    stable_since = time.monotonic()
    previous: tuple[str, ...] | None = None
    while time.monotonic() < deadline and not cancel.is_set():
        signature = None
        with suppress(RuntimeError, ValueError, KeyError, TypeError):
            node = runtime.kubectl(["get", "node", "lima-" + name, "-o", "json"], timeout=10)
            runtime.require(node)
            status = json.loads(node.stdout)["status"]
            ready = runtime.kubectl(["get", "--raw=/readyz"], timeout=10)
            if (
                ready.ok
                and ready.stdout.strip() == "ok"
                and status["nodeInfo"]["kubeletVersion"] == "v1.35.8"
                and any(
                    c["type"] == "Ready" and c["status"] == "True" for c in status["conditions"]
                )
            ):
                signature = ("ready",)
                if name == names[0]:
                    processes = runtime.guest(
                        name, ["sudo", "crictl", "ps", "-o", "json"], timeout=10
                    )
                    runtime.require(processes)
                    required = {
                        "kube-apiserver",
                        "kube-controller-manager",
                        "kube-scheduler",
                        "etcd",
                    }
                    components = {
                        c["labels"]["io.kubernetes.container.name"]: c["id"]
                        for c in json.loads(processes.stdout)["containers"]
                        if c.get("labels", {}).get("io.kubernetes.container.name") in required
                    }
                    signature = (
                        tuple(sorted(components.values()))
                        if components.keys() == required
                        else None
                    )
        if signature is None or signature != previous:
            stable_since = time.monotonic()
        elif time.monotonic() - stable_since >= 30:
            return
        previous = signature
        cancel.wait(2)
    raise RuntimeErrorBase(
        "The upgraded node and API did not remain ready for 30 seconds within three minutes."
    )
