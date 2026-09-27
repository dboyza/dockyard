"""Original maintenance assessment on an existing adjacent-version native cluster."""

from __future__ import annotations

import json
import time

from dockyard.fixtures.exam import apply
from dockyard.fixtures.maintenance import record
from dockyard.native import current
from dockyard.probes.kubernetes import kubectl


def prepare() -> None:
    r = current()
    record()
    primary = "d" + r.lab.id[:10] + "-cp1"
    apply(
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": "release-operator", "namespace": "dispatch"},
        }
    )
    kubectl(
        "patch",
        "service",
        "dispatch",
        "--type=merge",
        "-p",
        json.dumps({"spec": {"selector": {"release": "retired"}}}),
    )
    kubectl(
        "patch",
        "networkpolicy",
        "allow-dispatch-dependencies",
        "--type=json",
        "-p",
        json.dumps([{"op": "replace", "path": "/spec/egress/1/ports/0/port", "value": 6380}]),
    )
    # Deliberately remove the disruption contract while retaining both application replicas.
    kubectl("delete", "pdb", "dispatch-maintenance", "--ignore-not-found")
    r.require(r.guest(primary, ["sudo", "mkdir", "-p", "/var/lib/dockyard/maintenance-exam"]))
    r.require(
        r.guest(
            primary,
            [
                "sudo",
                "mv",
                "/etc/kubernetes/manifests/kube-scheduler.yaml",
                "/var/lib/dockyard/maintenance-exam/kube-scheduler.yaml",
            ],
        )
    )
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        process = r.guest(primary, ["sudo", "crictl", "ps", "--name", "^kube-scheduler$", "-q"])
        r.require(process)
        if not process.stdout.strip():
            break
        time.sleep(1)
    else:
        raise RuntimeError("The scheduler did not reach the intended stopped state.")
    print("Prepared the native maintenance exam with original objects and an adjacent upgrade.")


if __name__ == "__main__":
    prepare()
