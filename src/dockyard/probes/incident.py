"""Observe useful incident recovery and retained data, independently of repair commands."""

from __future__ import annotations

import json
import sys
import time
from contextlib import suppress
from typing import Any

from dockyard.fixtures.incident import baseline_path
from dockyard.probes.capacity import quantity
from dockyard.probes.kubernetes import available, get, job_roundtrip, kubectl, owned_pods, sql
from dockyard.probes.releases import endpoints, request


def observe(mode: str) -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(
        ("preserved", "available", "route", "workflow", "contract"), False
    )
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        baseline = json.loads(baseline_path().read_text())
        result["preserved"] = (
            get("namespace", "dispatch")["metadata"]["uid"] == baseline["namespace"]
            and get("pvc", "data-db-0")["metadata"]["uid"] == baseline["claim"]
            and sql(
                f"SELECT title FROM jobs WHERE id='{baseline['job']}'", workload="statefulset/db"
            )
            == "incident-preserved"
        )
    with suppress(RuntimeError, ValueError, KeyError, StopIteration):
        deployment, pods = owned_pods("dispatch")
        result["available"] = available(deployment, 2) and len(pods) == 2
        result["route"] = (
            result["available"]
            and endpoints("dispatch") == {p["metadata"]["uid"] for p in pods}
            and request(pods[0]["metadata"]["name"], "dispatch").get("service") == "dispatch"
        )
        if mode in {"readiness", "selector"}:
            contracts = []
            for pod in pods:
                api = next(c for c in pod["spec"]["containers"] if c["name"] == "api")
                probe = api.get("readinessProbe", {}).get("httpGet", {})
                port = probe.get("port")
                resolved = (
                    port
                    if isinstance(port, int)
                    else next(
                        (p["containerPort"] for p in api.get("ports", []) if p.get("name") == port),
                        None,
                    )
                )
                contracts.append(
                    probe.get("path") == "/readyz"
                    and resolved == 8080
                    and api.get("livenessProbe", {}).get("httpGet", {}).get("path") == "/healthz"
                    and api.get("startupProbe", {}).get("httpGet", {}).get("path") == "/startupz"
                )
            result["contract"] = len(contracts) == 2 and all(contracts)
        elif mode == "memory":
            worker, workers = owned_pods("worker")
            counts = {
                p["metadata"]["uid"]: [
                    s.get("restartCount", 0)
                    for s in p.get("status", {}).get("containerStatuses", [])
                ]
                for p in workers
            }
            bounded = []
            for pod in workers:
                container = next(c for c in pod["spec"]["containers"] if c["name"] == "worker")
                limits = container.get("resources", {}).get("limits", {})
                resident = int(
                    kubectl(
                        "exec",
                        pod["metadata"]["name"],
                        "-c",
                        "worker",
                        "--",
                        "python",
                        "-c",
                        "from pathlib import Path; print(next(line.split()[1] for line in "
                        "Path('/proc/1/status').read_text().splitlines() "
                        "if line.startswith('VmRSS:')))",
                    ).strip()
                )
                bounded.append(
                    128 * 1024**2 <= quantity(limits.get("memory", "0")) <= 256 * 1024**2
                    and 0
                    < quantity(
                        container.get("resources", {}).get("requests", {}).get("memory", "0")
                    )
                    <= quantity(limits.get("memory", "0"))
                    and resident >= 80 * 1024
                )
            time.sleep(10)
            _, after = owned_pods("worker")
            result["contract"] = (
                available(worker, 2)
                and len(workers) == 2
                and all(bounded)
                and counts
                == {
                    p["metadata"]["uid"]: [
                        s.get("restartCount", 0)
                        for s in p.get("status", {}).get("containerStatuses", [])
                    ]
                    for p in after
                }
                and all(
                    s.get("ready")
                    for p in after
                    for s in p.get("status", {}).get("containerStatuses", [])
                )
            )
    if mode == "claim":
        result["contract"] = archive()
    result["workflow"] = job_roundtrip(database_workload="statefulset/db")
    return result


def archive(claim_name: str = "archive", workload: str = "archiver") -> bool:
    """Write through the workload mount and read through a separate consumer of its claim."""
    import os
    import uuid

    from dockyard.process import run

    reader = "archive-observation-" + uuid.uuid4().hex[:10]
    marker = uuid.uuid4().hex
    try:
        baseline = json.loads(baseline_path().read_text())
        claim = get("pvc", claim_name)
        deployment, pods = owned_pods(workload)
        if (
            claim["metadata"]["uid"] != baseline[claim_name]
            or claim["status"]["phase"] != "Bound"
            or not available(deployment, 1)
            or len(pods) != 1
        ):
            return False
        pod = pods[0]
        spec = pod["spec"]
        mount = next(
            m
            for c in spec["containers"]
            for m in c.get("volumeMounts", [])
            if m["mountPath"] == "/archive"
        )
        if not any(
            v["name"] == mount["name"]
            and v.get("persistentVolumeClaim", {}).get("claimName") == claim_name
            for v in spec.get("volumes", [])
        ):
            return False
        kubectl(
            "exec",
            pod["metadata"]["name"],
            "--",
            "python",
            "-c",
            f"from pathlib import Path; Path('/archive/{reader}').write_text({marker!r})",
        )
        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": reader, "namespace": "dispatch"},
            "spec": {
                "restartPolicy": "Never",
                "securityContext": {"fsGroup": 10001},
                "nodeName": spec["nodeName"],
                "terminationGracePeriodSeconds": 0,
                "containers": [
                    {
                        "name": "reader",
                        "image": os.environ["DOCKYARD_IMAGE"],
                        "imagePullPolicy": "Never",
                        "command": [
                            "python",
                            "-c",
                            f"from pathlib import Path; p=Path('/archive/{reader}'); "
                            "print(p.read_text()); p.unlink()",
                        ],
                        "volumeMounts": [{"name": "archive", "mountPath": "/archive"}],
                    }
                ],
                "volumes": [
                    {"name": "archive", "persistentVolumeClaim": {"claimName": claim_name}}
                ],
            },
        }
        created = run(["kubectl", "create", "-f", "-"], input_text=json.dumps(manifest))
        if not created.ok:
            return False
        kubectl(
            "wait",
            "pod/" + reader,
            "--for=jsonpath={.status.phase}=Succeeded",
            "--timeout=45s",
            timeout=50,
        )
        return kubectl("logs", reader) == marker
    except (RuntimeError, ValueError, KeyError, StopIteration, OSError):
        return False
    finally:
        with suppress(RuntimeError):
            kubectl(
                "delete",
                "pod",
                reader,
                "--ignore-not-found",
                "--wait=true",
                "--timeout=20s",
                timeout=25,
            )


if __name__ == "__main__":
    if sys.argv[1:] not in (["readiness"], ["selector"], ["memory"], ["network"], ["claim"]):
        raise SystemExit("Unknown packaged incident observation.")
    print(json.dumps(observe(sys.argv[1])))
