"""Verify restored object identity, live control-plane behavior, and fresh scheduling."""

from __future__ import annotations

import json
import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import yaml

from dockyard.fixtures.recovery import etcd
from dockyard.native import current
from dockyard.probes.bootstrap import ERRORS
from dockyard.probes.maintenance import maintenance, observed


@contextmanager
def measured(result: dict[str, Any], key: str) -> Iterator[None]:
    try:
        yield
    except ERRORS as error:
        result["_details"][key] = {"observation_error": str(error)[-1200:]}


def recovery(mode: str) -> dict[str, Any]:
    result = maintenance("recovery")
    result.update(dict.fromkeys(("components", "scheduled", "restored"), False))
    runtime = current()
    primary = "d" + runtime.lab.id[:10] + "-cp1"
    with measured(result, "components"):
        active = runtime.guest(primary, ["systemctl", "is-active", "kubelet"])
        ready = runtime.kubectl(["get", "--raw=/readyz"])
        containers = runtime.guest(primary, ["sudo", "crictl", "ps", "-o", "json"])
        runtime.require(containers)
        names = {c["metadata"]["name"] for c in json.loads(containers.stdout)["containers"]}
        result["_details"]["components"] = {
            "kubelet_active": active.ok,
            "api_ready": ready.ok,
            "running_components": sorted(
                names
                & {
                    "etcd",
                    "kube-apiserver",
                    "kube-controller-manager",
                    "kube-scheduler",
                }
            ),
        }
        result["components"] = bool(
            active.ok
            and ready.ok
            and {
                "etcd",
                "kube-apiserver",
                "kube-controller-manager",
                "kube-scheduler",
            }.issubset(names)
        )
    if mode in {"etcd", "mission"}:
        with measured(result, "restored"):
            snapshot = json.loads((runtime.root / "data/recovery-snapshot.json").read_text())
            endpoint = json.loads(
                etcd(
                    runtime,
                    [
                        "etcdctl",
                        "--endpoints=https://127.0.0.1:2379",
                        "--cacert=/etc/kubernetes/pki/etcd/ca.crt",
                        "--cert=/etc/kubernetes/pki/etcd/server.crt",
                        "--key=/etc/kubernetes/pki/etcd/server.key",
                        "endpoint",
                        "status",
                        "-w",
                        "json",
                    ],
                )
            )[0]["Status"]
            compacted = False
            try:
                etcd(
                    runtime,
                    [
                        "etcdctl",
                        "--endpoints=https://127.0.0.1:2379",
                        "--cacert=/etc/kubernetes/pki/etcd/ca.crt",
                        "--cert=/etc/kubernetes/pki/etcd/server.crt",
                        "--key=/etc/kubernetes/pki/etcd/server.key",
                        "get",
                        "/registry/namespaces/dispatch",
                        "--rev=" + str(snapshot["revision"]),
                    ],
                )
            except RuntimeError as error:
                compacted = "required revision has been compacted" in str(error)
            # Revision advancement and the original UID jointly distinguish a restore
            # from recreating a similarly named object or merely copying a snapshot.
            result["restored"] = bool(
                result["preserved"]
                and endpoint["header"]["revision"] > snapshot["revision"] + 1000000
                and compacted
            )
            result["_details"]["restored"] = {
                "snapshot_revision": snapshot["revision"],
                "live_revision": endpoint["header"]["revision"],
                "original_state_preserved": result["preserved"],
                "snapshot_revision_compacted": compacted,
            }
    name = "dockyard-schedule-" + uuid.uuid4().hex[:12]
    with measured(result, "scheduled"):
        source = observed(runtime, ["get", "deployment", "trusted-client", "-n", "frontend"])
        pod = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": name, "namespace": "frontend"},
            "spec": source["spec"]["template"]["spec"],
        }
        # No nodeName is supplied: the scheduler must perform a new assignment.
        pod["spec"].pop("nodeName", None)
        pod["spec"]["terminationGracePeriodSeconds"] = 0
        runtime.require(runtime.kubectl(["create", "-f", "-"], payload=yaml.safe_dump(pod)))
        try:
            wait = runtime.kubectl(
                [
                    "wait",
                    "pod/" + name,
                    "-n",
                    "frontend",
                    "--for=condition=PodScheduled",
                    "--timeout=12s",
                ],
                timeout=20,
            )
            actual = observed(runtime, ["get", "pod", name, "-n", "frontend"])
            result["scheduled"] = bool(wait.ok and actual["spec"].get("nodeName"))
            result["_details"]["scheduled"] = {
                "assigned_node": actual["spec"].get("nodeName"),
                "wait_completed": wait.ok,
                "conditions": actual.get("status", {}).get("conditions", []),
            }
        finally:
            runtime.kubectl(
                ["delete", "pod", name, "-n", "frontend", "--wait=true", "--timeout=30s"],
                timeout=35,
            )
    return result


if __name__ == "__main__":
    print(json.dumps(recovery(sys.argv[1])))
