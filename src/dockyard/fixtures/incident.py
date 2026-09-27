"""Establish real broken Kubernetes incident states and preservation baselines."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

from dockyard.probes.kubernetes import get, kubectl, owned_pods, sql
from dockyard.workspace import atomic_write


def baseline_path() -> Path:
    return (
        Path(os.environ["DOCKYARD_DATA"])
        / "labs"
        / os.environ["DOCKYARD_LAB"]
        / "data/incident.json"
    )


def prepare(mode: str) -> None:
    for resource in ("statefulset/db", "deployment/dispatch", "deployment/worker"):
        kubectl("rollout", "status", resource, "--timeout=120s", timeout=130)
    marker = uuid.uuid4().hex
    sql(
        f"INSERT INTO jobs(id,title,status) VALUES ('{marker}','incident-preserved','done')",
        workload="statefulset/db",
    )
    baseline = {
        "namespace": get("namespace", "dispatch")["metadata"]["uid"],
        "claim": get("pvc", "data-db-0")["metadata"]["uid"],
        "job": marker,
        "mode": mode,
    }
    atomic_write(baseline_path(), json.dumps(baseline).encode())
    if mode == "readiness":
        patch = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "api",
                                "ports": [
                                    {"name": "http", "containerPort": 8080},
                                    {"name": "metrics", "containerPort": 9090},
                                ],
                                "readinessProbe": {
                                    "httpGet": {"path": "/readyz", "port": "metrics"}
                                },
                            }
                        ]
                    }
                }
            }
        }
        kubectl("patch", "deployment", "dispatch", "--type=strategic", "-p", json.dumps(patch))
        # Remove the earlier ready replicas so the outage is stable and inspectable.
        kubectl("scale", "deployment/dispatch", "--replicas=0")
        kubectl("wait", "pod", "-l", "app=dispatch", "--for=delete", "--timeout=60s", timeout=65)
        kubectl("scale", "deployment/dispatch", "--replicas=2")
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            _, pods = owned_pods("dispatch")
            if len(pods) == 2 and all(
                any(s.get("started") for s in p.get("status", {}).get("containerStatuses", []))
                for p in pods
            ):
                break
            time.sleep(1)
        else:
            raise RuntimeError("The broken readiness fixture never completed application startup.")
    elif mode == "selector":
        kubectl(
            "patch",
            "service",
            "dispatch",
            "--type=merge",
            "-p",
            json.dumps({"spec": {"selector": {"release-channel": "current"}}}),
        )
    elif mode in {"registry", "baseline"}:
        return
    elif mode == "claim":
        nodes = get("nodes")["items"]
        node = nodes[-1]["metadata"]["name"]
        kubectl("label", "node", node, "dockyard.io/storage-tier=warm", "--overwrite")
        manifest = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": "archive", "namespace": "dispatch"},
            "spec": {
                "storageClassName": "standard",
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": "128Mi"}},
            },
        }
        from dockyard.process import run

        applied = run(["kubectl", "apply", "-f", "-"], input_text=json.dumps(manifest))
        if not applied.ok:
            raise RuntimeError(applied.stderr)
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "archiver", "namespace": "dispatch"},
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "archiver"}},
                "template": {
                    "metadata": {"labels": {"app": "archiver"}},
                    "spec": {
                        "nodeSelector": {"dockyard.io/storage-tier": "cold"},
                        "securityContext": {"fsGroup": 10001},
                        "containers": [
                            {
                                "name": "archiver",
                                "image": os.environ["DOCKYARD_IMAGE"],
                                "imagePullPolicy": "Never",
                                "command": ["python", "-c", "import time; time.sleep(86400)"],
                                "resources": {
                                    "requests": {"cpu": "10m", "memory": "16Mi"},
                                    "limits": {"cpu": "100m", "memory": "64Mi"},
                                },
                                "volumeMounts": [{"name": "archive", "mountPath": "/archive"}],
                            }
                        ],
                        "volumes": [
                            {"name": "archive", "persistentVolumeClaim": {"claimName": "archive"}}
                        ],
                    },
                },
            },
        }
        applied = run(["kubectl", "apply", "-f", "-"], input_text=json.dumps(deployment))
        if not applied.ok:
            raise RuntimeError(applied.stderr)
        baseline["archive"] = get("pvc", "archive")["metadata"]["uid"]
        atomic_write(baseline_path(), json.dumps(baseline).encode())
    elif mode == "network":
        kubectl(
            "patch",
            "networkpolicy",
            "allow-dns",
            "--type=json",
            "-p",
            json.dumps(
                [
                    {
                        "op": "replace",
                        "path": "/spec/egress/0/ports",
                        "value": [{"protocol": "TCP", "port": 53}],
                    }
                ]
            ),
        )
        kubectl(
            "patch",
            "networkpolicy",
            "allow-worker-dependencies",
            "--type=json",
            "-p",
            json.dumps([{"op": "replace", "path": "/spec/egress/1/ports/0/port", "value": 6380}]),
        )
    elif mode == "memory":
        patch = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "worker",
                                "command": [
                                    "python",
                                    "-c",
                                    "import runpy; working_set = bytearray(80 * 1024 * 1024); "
                                    "runpy.run_path('worker.py', run_name='__main__')",
                                ],
                                "resources": {"limits": {"memory": "64Mi"}},
                            }
                        ]
                    }
                }
            }
        }
        kubectl("patch", "deployment", "worker", "--type=strategic", "-p", json.dumps(patch))
        kubectl("scale", "deployment/worker", "--replicas=0")
        kubectl("wait", "pod", "-l", "app=worker", "--for=delete", "--timeout=60s", timeout=65)
        kubectl("scale", "deployment/worker", "--replicas=2")
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            _, pods = owned_pods("worker")
            killed = [
                s.get("lastState", {}).get("terminated", {}).get("reason") == "OOMKilled"
                or s.get("state", {}).get("terminated", {}).get("reason") == "OOMKilled"
                for p in pods
                for s in p.get("status", {}).get("containerStatuses", [])
            ]
            if killed and all(killed):
                break
            time.sleep(1)
        else:
            raise RuntimeError("The worker fixture did not demonstrate an actual OOM kill.")
    else:
        raise ValueError("Unknown incident fixture.")
    print("Prepared the isolated incident and recorded the original database identity.")


if __name__ == "__main__":
    prepare(sys.argv[1])
