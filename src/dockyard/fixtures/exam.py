"""Original exam environments with independent task objects and real failure states."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from dockyard.fixtures.incident import baseline_path, prepare
from dockyard.probes.kubernetes import get, kubectl
from dockyard.process import run
from dockyard.workspace import atomic_write


def apply(*documents: dict[str, Any]) -> None:
    result = run(["kubectl", "apply", "-f", "-"], input_text=yaml.safe_dump_all(documents))
    if not result.ok:
        raise RuntimeError(result.stderr)


def deployment(
    name: str, command: list[str], *, labels: dict[str, str] | None = None
) -> dict[str, Any]:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": "dispatch"},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {"labels": {"app": name, **(labels or {})}},
                "spec": {
                    "securityContext": {
                        "runAsNonRoot": True,
                        "seccompProfile": {"type": "RuntimeDefault"},
                    },
                    "containers": [
                        {
                            "name": name,
                            "image": os.environ["DOCKYARD_IMAGE"],
                            "imagePullPolicy": "Never",
                            "command": command,
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "capabilities": {"drop": ["ALL"]},
                            },
                            "resources": {
                                "requests": {"cpu": "10m", "memory": "16Mi"},
                                "limits": {"cpu": "100m", "memory": "128Mi"},
                            },
                        }
                    ],
                },
            },
        },
    }


def ckad_a() -> None:
    prepare("baseline")
    # Every task has its own specific outcome; no course mission is renamed as an exam.
    Path("VERSION").write_text("dispatch-exam-a\n")
    dockerfile = Path("Dockerfile")
    dockerfile.write_text(
        dockerfile.read_text().replace('CMD ["python", "app.py"]', 'CMD ["python", "missing.py"]')
    )
    kubectl(
        "patch",
        "configmap",
        "dispatch-settings",
        "--type=merge",
        "-p",
        json.dumps({"data": {"environment": "staging", "banner.txt": "Release preview only"}}),
    )
    kubectl(
        "patch",
        "deployment",
        "dispatch",
        "--type=strategic",
        "-p",
        json.dumps(
            {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": "api",
                                    "readinessProbe": {
                                        "httpGet": {"path": "/healthz", "port": 8080}
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        ),
    )
    kubectl(
        "patch",
        "service",
        "dispatch",
        "--type=merge",
        "-p",
        json.dumps({"spec": {"ports": [{"port": 8080, "targetPort": 8099}]}}),
    )
    reporter = deployment("reporter", ["python", "-c", "import time; time.sleep(86400)"])
    spec = reporter["spec"]["template"]["spec"]
    spec["securityContext"] = {"fsGroup": 10001}
    spec["containers"][0]["volumeMounts"] = [{"name": "reports", "mountPath": "/archive"}]
    spec["volumes"] = [{"name": "reports", "emptyDir": {}}]
    claim = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": "reports", "namespace": "dispatch"},
        "spec": {
            "storageClassName": "standard",
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": "128Mi"}},
        },
    }
    audit = deployment("audit-target", ["python", "-m", "http.server", "8080"])
    trusted = deployment(
        "audit-reader",
        ["python", "-c", "import time; time.sleep(86400)"],
        labels={"role": "audit-reader"},
    )
    denied = deployment(
        "audit-outsider",
        ["python", "-c", "import time; time.sleep(86400)"],
        labels={"role": "outsider"},
    )
    cron = {
        "apiVersion": "batch/v1",
        "kind": "CronJob",
        "metadata": {"name": "release-audit", "namespace": "dispatch"},
        "spec": {
            "schedule": "*/5 * * * *",
            "suspend": True,
            "concurrencyPolicy": "Allow",
            "jobTemplate": {
                "spec": {
                    "backoffLimit": 1,
                    "template": {
                        "spec": {
                            "restartPolicy": "Never",
                            "containers": [
                                {
                                    "name": "audit",
                                    "image": os.environ["DOCKYARD_IMAGE"],
                                    "imagePullPolicy": "Never",
                                    "command": [
                                        "python",
                                        "-c",
                                        "import urllib.request; print(urllib.request.urlopen('http://dispatch:8080/healthz',timeout=3).read().decode())",
                                    ],
                                }
                            ],
                        }
                    },
                }
            },
        },
    }
    policy = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": "audit-access", "namespace": "dispatch"},
        "spec": {
            "podSelector": {"matchLabels": {"app": "audit-target"}},
            "policyTypes": ["Ingress"],
            "ingress": [
                {"from": [{"podSelector": {}}], "ports": [{"protocol": "TCP", "port": 8080}]}
            ],
        },
    }
    apply(claim, reporter, audit, trusted, denied, cron, policy)
    baseline = json.loads(baseline_path().read_text())
    baseline["reports"] = get("pvc", "reports")["metadata"]["uid"]
    atomic_write(baseline_path(), json.dumps(baseline).encode())
    for name in ("reporter", "audit-target", "audit-reader", "audit-outsider", "dispatch"):
        kubectl("rollout", "status", "deployment/" + name, "--timeout=120s", timeout=130)
    print("Prepared the original application-release exam task set.")


if __name__ == "__main__":
    if sys.argv[1:] != ["ckad-a"]:
        raise SystemExit("Unknown authored exam fixture.")
    ckad_a()
