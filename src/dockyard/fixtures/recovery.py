"""Prepare bounded control-plane failures after recording recoverable state."""

from __future__ import annotations

import json
import sys
import time

from dockyard.fixtures.maintenance import record
from dockyard.native import current
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.workspace import atomic_write


def etcd(runtime: LinuxRuntime, args: list[str]) -> str:
    primary = "d" + runtime.lab.id[:10] + "-cp1"
    found = runtime.guest(primary, ["sudo", "crictl", "ps", "--name", "^etcd$", "-q"])
    runtime.require(found)
    containers = found.stdout.split()
    if len(containers) != 1:
        raise RuntimeError("Expected one running etcd member on the recorded primary.")
    result = runtime.guest(primary, ["sudo", "crictl", "exec", containers[0], *args])
    runtime.require(result)
    return result.stdout


def snapshot(runtime: LinuxRuntime) -> None:
    etcd(
        runtime,
        [
            "etcdctl",
            "--endpoints=https://127.0.0.1:2379",
            "--cacert=/etc/kubernetes/pki/etcd/ca.crt",
            "--cert=/etc/kubernetes/pki/etcd/server.crt",
            "--key=/etc/kubernetes/pki/etcd/server.key",
            "snapshot",
            "save",
            "/var/lib/etcd/dockyard-recovery.db",
        ],
    )
    status = json.loads(
        etcd(
            runtime,
            [
                "etcdutl",
                "snapshot",
                "status",
                "/var/lib/etcd/dockyard-recovery.db",
                "-w",
                "json",
            ],
        )
    )
    atomic_write(runtime.root / "data/recovery-snapshot.json", json.dumps(status).encode())


def prepare(mode: str) -> None:
    runtime = current()
    primary = "d" + runtime.lab.id[:10] + "-cp1"
    if mode == "stage-loss":
        status = json.loads(
            etcd(
                runtime,
                [
                    "etcdutl",
                    "snapshot",
                    "status",
                    "/var/lib/etcd/dockyard-recovery.db",
                    "-w",
                    "json",
                ],
            )
        )
        if status.get("revision", 0) <= 0 or status.get("totalKey", 0) <= 0:
            raise RuntimeError("Take and inspect a valid snapshot before staging state loss.")
        atomic_write(runtime.root / "data/recovery-snapshot.json", json.dumps(status).encode())
        runtime.require(
            runtime.kubectl(["delete", "configmap", "maintenance-sentinel", "-n", "default"])
        )
        print("Removed the original sentinel. Restore its original identity from the snapshot.")
        return
    record()
    runtime.require(runtime.guest(primary, ["sudo", "mkdir", "-p", "/var/lib/dockyard"]))
    if mode == "etcd":
        return
    if mode == "mission":
        snapshot(runtime)
        runtime.require(
            runtime.kubectl(["delete", "configmap", "maintenance-sentinel", "-n", "default"])
        )
    if mode in {"static-pods", "mission"}:
        runtime.require(
            runtime.guest(primary, ["sudo", "mkdir", "-p", "/var/lib/dockyard/recovery"])
        )
        runtime.require(
            runtime.guest(
                primary,
                [
                    "sudo",
                    "mv",
                    "/etc/kubernetes/manifests/kube-scheduler.yaml",
                    "/var/lib/dockyard/recovery/kube-scheduler.yaml",
                ],
            )
        )
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            found = runtime.guest(
                primary, ["sudo", "crictl", "ps", "--name", "^kube-scheduler$", "-q"]
            )
            runtime.require(found)
            if not found.stdout.strip():
                break
            time.sleep(1)
        else:
            raise RuntimeError("The scheduler did not stop after its manifest was moved.")
    if mode == "static-pods":
        runtime.require(runtime.guest(primary, ["sudo", "systemctl", "stop", "kubelet"]))
    if mode in {"api", "mission"}:
        runtime.require(
            runtime.guest(
                primary,
                [
                    "sudo",
                    "python3",
                    "-c",
                    """
from pathlib import Path
p = Path('/etc/kubernetes/manifests/kube-apiserver.yaml')
s = p.read_text()
old = '--etcd-servers=https://127.0.0.1:2379'
assert s.count(old) == 1
t = Path('/var/lib/dockyard/apiserver-fault.yaml')
t.write_text(s.replace(old, '--etcd-servers=https://127.0.0.1:2399'))
t.replace(p)
""",
                ],
            )
        )
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            status = runtime.kubectl(["get", "--raw=/readyz", "--request-timeout=2s"], timeout=5)
            if not status.ok:
                break
            time.sleep(1)
        else:
            raise RuntimeError("The API did not enter the intended unavailable state.")
    print("Prepared the declared control-plane failure on this lab's owned primary.")


if __name__ == "__main__":
    if sys.argv[1:] not in (["etcd"], ["static-pods"], ["api"], ["mission"], ["stage-loss"]):
        raise SystemExit("Choose etcd, static-pods, api, mission, or stage-loss.")
    prepare(sys.argv[1])
