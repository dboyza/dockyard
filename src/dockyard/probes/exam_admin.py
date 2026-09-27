"""Grade native operations by actual privileges, processes, backups, and traffic."""

from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

from dockyard.fixtures.recovery import etcd
from dockyard.native import current
from dockyard.probes.bootstrap import ERRORS
from dockyard.probes.kubernetes import available, get, kubectl, owned_pods
from dockyard.probes.maintenance import maintenance
from dockyard.probes.security import connections
from dockyard.process import run


def can(verb: str, resource: str) -> bool:
    r = current()
    resource, _, subresource = resource.partition("/")
    return (
        r.kubectl(
            [
                "auth",
                "can-i",
                verb,
                resource,
                *(["--subresource=" + subresource] if subresource else []),
                "-n",
                "dispatch",
                "--as=system:serviceaccount:dispatch:incident-observer",
            ]
        ).stdout.strip()
        == "yes"
    )


def operations() -> dict[str, Any]:
    r = current()
    result = maintenance("exam")
    result.update(
        dict.fromkeys(
            ("backup", "rbac", "dns", "storage", "agents", "placement", "chart", "transport"), False
        )
    )
    primary = "d" + r.lab.id[:10] + "-cp1"
    worker = "d" + r.lab.id[:10] + "-worker"
    with suppress(*ERRORS):
        baseline = json.loads((r.root / "data/exam-backup.json").read_text())
        status = json.loads(
            etcd(
                r, ["etcdutl", "snapshot", "status", "/var/lib/etcd/operations-a.db", "-w", "json"]
            )
        )
        result["backup"] = (
            status["revision"] >= baseline["revision"]
            and status["totalKey"] > 0
            and status["hash"] > 0
        )
    with suppress(*ERRORS):
        result["rbac"] = all(
            can(v, res)
            for v, res in [
                ("get", "pods"),
                ("list", "pods"),
                ("watch", "pods"),
                ("get", "pods/log"),
            ]
        ) and not any(
            can(v, res)
            for v, res in [
                ("get", "secrets"),
                ("create", "pods"),
                ("delete", "pods"),
                ("update", "deployments.apps"),
            ]
        )
    with suppress(*ERRORS):
        raw = kubectl(
            "exec",
            "deployment/trusted-client",
            "-n",
            "frontend",
            "--",
            "python",
            "-c",
            "import socket; print(socket.gethostbyname('dispatch.dispatch.svc.cluster.local'))",
        )
        result["dns"] = raw == get("service", "dispatch")["spec"]["clusterIP"]
    with suppress(*ERRORS):
        baseline = json.loads((r.root / "data/exam-backup.json").read_text())
        db = get("statefulset", "db")
        pod = get("pod", "db-0")
        claim = get("pvc", "data-db-0")
        pv = get("pv", claim["spec"]["volumeName"])
        result["storage"] = (
            db.get("status", {}).get("readyReplicas") == 1
            and pod["spec"]["nodeName"] == "lima-" + worker
            and claim["status"]["phase"] == "Bound"
            and claim["metadata"]["uid"] == baseline["claim_uid"]
            and pv["metadata"]["uid"] == baseline["volume_uid"]
            and pv["spec"]["claimRef"]["uid"] == claim["metadata"]["uid"]
            and result["preserved"]
        )
    with suppress(*ERRORS):
        ds = get("daemonset", "node-observer")
        pods = [
            p
            for p in get("pods")["items"]
            if any(
                o["uid"] == ds["metadata"]["uid"] for o in p["metadata"].get("ownerReferences", [])
            )
        ]
        nodes = {"lima-" + primary, "lima-" + worker}
        result["agents"] = (
            len(pods) == 2
            and {p["spec"]["nodeName"] for p in pods} == nodes
            and all(
                any(
                    c["type"] == "Ready" and c["status"] == "True"
                    for c in p["status"].get("conditions", [])
                )
                and kubectl(
                    "exec",
                    p["metadata"]["name"],
                    "--",
                    "python",
                    "-c",
                    "from pathlib import Path; print(Path('/proc/1/comm').read_text().strip())",
                )
                == "python"
                for p in pods
            )
        )
    with suppress(*ERRORS):
        d, pods = owned_pods("batch-audit")
        node = get("node", "lima-" + worker)
        result["placement"] = (
            available(d, 1)
            and len(pods) == 1
            and pods[0]["spec"]["nodeName"] == "lima-" + worker
            and pods[0]["spec"].get("nodeSelector", {}).get("dockyard.io/pool") == "batch"
            and any(
                t.get("key") == "dockyard.io/batch" and t.get("effect") == "NoSchedule"
                for t in node["spec"].get("taints", [])
            )
            and any(
                t.get("key") == "dockyard.io/batch"
                and t.get("effect") == "NoSchedule"
                and (t.get("operator") == "Exists" or t.get("value") == "true")
                for t in pods[0]["spec"].get("tolerations", [])
            )
        )
    with suppress(*ERRORS):
        release = run(["helm", "status", "operations-report", "-n", "dispatch", "-o", "json"])
        d, pods = owned_pods("operations-report")
        value = kubectl(
            "exec",
            "deployment/operations-report",
            "--",
            "python",
            "-c",
            "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/environment').read().decode())",
        )
        result["chart"] = (
            release.ok
            and json.loads(release.stdout)["info"]["status"] == "deployed"
            and available(d, 1)
            and value == "production"
            and d["metadata"].get("annotations", {}).get("meta.helm.sh/release-name")
            == "operations-report"
        )
    with suppress(*ERRORS):
        forwarding = r.guest(worker, ["sysctl", "-n", "net.ipv4.ip_forward"])
        # Existing frontend is on the control-plane node; API Pods are on the worker.
        result["transport"] = (
            forwarding.ok
            and forwarding.stdout.strip() == "1"
            and connections(
                "trusted-client", "frontend", [("dispatch.dispatch.svc.cluster.local", 8080)]
            )
            == [True]
            and result["workflow"]
        )
    return result


if __name__ == "__main__":
    print(json.dumps(operations()))
