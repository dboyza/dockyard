"""Explicit infrastructure faults and preservation records for owned native lessons."""

from __future__ import annotations

import json
import sys
import time
from contextlib import suppress
from pathlib import Path

from dockyard.fixtures.maintenance import record
from dockyard.native import current
from dockyard.probes.maintenance import observed
from dockyard.workspace import atomic_write


def prepare(mode: str) -> None:
    record()
    runtime = current()
    primary = "d" + runtime.lab.id[:10] + "-cp1"
    worker = "d" + runtime.lab.id[:10] + "-worker"
    if mode in {"storage", "mission"}:
        path = runtime.root / "data/maintenance-baseline.json"
        baseline = json.loads(path.read_text())
        claim = observed(runtime, ["get", "pvc", "data-db-0"])
        volume = observed(runtime, ["get", "pv", claim["spec"]["volumeName"]])
        baseline["storage"] = {
            "claim_uid": claim["metadata"]["uid"],
            "volume_uid": volume["metadata"]["uid"],
            "handle": volume["spec"]["csi"]["volumeHandle"],
        }
        atomic_write(path, json.dumps(baseline).encode())
        runtime.require(
            runtime.kubectl(
                [
                    "patch",
                    "statefulset",
                    "db",
                    "--type=merge",
                    "-p",
                    json.dumps(
                        {
                            "spec": {
                                "template": {
                                    "spec": {
                                        "nodeSelector": {
                                            "kubernetes.io/hostname": "lima-" + primary
                                        }
                                    }
                                }
                            }
                        }
                    ),
                ]
            )
        )
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            with suppress(RuntimeError, ValueError, KeyError):
                pod = observed(runtime, ["get", "pod", "db-0"])
                if pod["spec"].get("nodeSelector", {}).get(
                    "kubernetes.io/hostname"
                ) == "lima-" + primary and not pod["metadata"].get("deletionTimestamp"):
                    break
            time.sleep(1)
        else:
            raise RuntimeError(
                "The database did not reach the intended misplaced replacement state."
            )
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            attachments = observed(runtime, ["get", "volumeattachments"])["items"]
            if not any(
                item["spec"]["source"].get("persistentVolumeName") == volume["metadata"]["name"]
                for item in attachments
            ):
                break
            time.sleep(1)
        else:
            raise RuntimeError("The previous database attachment did not finish detaching.")
    if mode == "packets":
        runtime.require(
            runtime.guest(
                primary,
                [
                    "sudo",
                    "iptables",
                    "-t",
                    "raw",
                    "-I",
                    "PREROUTING",
                    "1",
                    "-p",
                    "udp",
                    "--dport",
                    "4789",
                    "-m",
                    "comment",
                    "--comment",
                    "dockyard-" + runtime.lab.id + "-vxlan",
                    "-j",
                    "DROP",
                ],
            )
        )
    if mode == "dns":
        config = observed(runtime, ["get", "configmap", "coredns", "-n", "kube-system"])
        corefile = config["data"]["Corefile"]
        Path("Corefile.original").write_text(corefile)
        changed = corefile.replace("kubernetes cluster.local", "kubernetes wrong.local")
        if changed == corefile:
            raise RuntimeError(
                "The pinned CoreDNS configuration did not contain the expected zone."
            )
        runtime.require(
            runtime.kubectl(
                [
                    "patch",
                    "configmap",
                    "coredns",
                    "-n",
                    "kube-system",
                    "--type=merge",
                    "-p",
                    json.dumps({"data": {"Corefile": changed}}),
                ]
            )
        )
        runtime.require(
            runtime.kubectl(["rollout", "restart", "deployment/coredns", "-n", "kube-system"])
        )
        runtime.require(
            runtime.kubectl(
                ["rollout", "status", "deployment/coredns", "-n", "kube-system", "--timeout=120s"],
                timeout=130,
            )
        )
        runtime.require(
            runtime.kubectl(
                [
                    "patch",
                    "daemonset",
                    "kube-proxy",
                    "-n",
                    "kube-system",
                    "--type=strategic",
                    "-p",
                    json.dumps(
                        {
                            "spec": {
                                "template": {
                                    "spec": {
                                        "containers": [
                                            {
                                                "name": "kube-proxy",
                                                "image": "dockyard-invalid/kube-proxy:missing",
                                                "imagePullPolicy": "Never",
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    ),
                ]
            )
        )
    if mode == "mission":
        runtime.require(
            runtime.kubectl(
                [
                    "patch",
                    "deployment",
                    "trusted-client",
                    "-n",
                    "frontend",
                    "--type=merge",
                    "-p",
                    json.dumps({"spec": {"template": {"spec": {"dnsPolicy": "Default"}}}}),
                ]
            )
        )
        runtime.require(
            runtime.kubectl(
                [
                    "rollout",
                    "status",
                    "deployment/trusted-client",
                    "-n",
                    "frontend",
                    "--timeout=90s",
                ],
                timeout=100,
            )
        )
        runtime.require(runtime.guest(worker, ["sudo", "sysctl", "-w", "net.ipv4.ip_forward=0"]))
    print("Prepared the declared infrastructure fault and preserved the original state record.")


if __name__ == "__main__":
    if sys.argv[1:] not in (["packets"], ["dns"], ["storage"], ["mission"]):
        raise SystemExit("Choose the packaged packets, dns, storage, or mission fixture.")
    prepare(sys.argv[1])
