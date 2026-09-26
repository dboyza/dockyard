"""Observe cross-node packets, new Service programming, and actual CSI-mounted storage."""

from __future__ import annotations

import json
import time
import uuid
from contextlib import suppress
from typing import Any

from dockyard.native import current
from dockyard.probes.bootstrap import ERRORS
from dockyard.probes.maintenance import maintenance, observed
from dockyard.probes.security import execute


def healthy_http(host: str) -> bool:
    url = "http://" + host + ":8080/healthz"
    result = execute(
        "trusted-client",
        "import json,urllib.request; "
        + f"print(urllib.request.urlopen({url!r},timeout=3).read().decode())",
        "frontend",
    )
    return bool(result.get("status") == "ok" and result.get("service") == "dispatch")


def infrastructure() -> dict[str, Any]:
    runtime = current()
    result = maintenance("infrastructure")
    result.update(dict.fromkeys(("packets", "dns", "proxy", "csi"), False))
    details = result["_details"]
    with suppress(*ERRORS):
        pods = observed(runtime, ["get", "pods", "-l", "app=dispatch,track=stable"])["items"]
        pod = next(
            pod
            for pod in pods
            if pod.get("status", {}).get("podIP") and not pod["metadata"].get("deletionTimestamp")
        )
        clients = observed(runtime, ["get", "pods", "-n", "frontend", "-l", "app=trusted"])["items"]
        client = next(item for item in clients if not item["metadata"].get("deletionTimestamp"))
        source = "lima-d" + runtime.lab.id[:10] + "-cp1"
        target = "lima-d" + runtime.lab.id[:10] + "-worker"
        result["packets"] = bool(
            client["spec"]["nodeName"] == source
            and pod["spec"]["nodeName"] == target
            and healthy_http(pod["status"]["podIP"])
        )
        details["packets"] = {
            "source_node": client["spec"]["nodeName"],
            "destination_node": pod["spec"]["nodeName"],
            "direct_pod_http": result["packets"],
        }
    name = "dockyard-route-" + uuid.uuid4().hex[:12]
    created = False
    try:
        with suppress(*ERRORS):
            service = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {"name": name, "namespace": "dispatch"},
                "spec": {
                    "selector": {"app": "dispatch", "track": "stable"},
                    "publishNotReadyAddresses": True,
                    "ports": [{"port": 8080, "targetPort": 8080}],
                },
            }
            applied = runtime.kubectl(["create", "-f", "-"], payload=json.dumps(service))
            runtime.require(applied)
            created = True
            address = observed(runtime, ["get", "service", name])["spec"]["clusterIP"]
            hostname = name + ".dispatch.svc.cluster.local"
            with suppress(*ERRORS):
                resolution = execute(
                    "trusted-client",
                    "import json,socket; print(json.dumps(socket.gethostbyname("
                    + repr(hostname)
                    + ")))",
                    "frontend",
                )
                result["dns"] = resolution == address
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                with suppress(*ERRORS):
                    result["proxy"] = healthy_http(address)
                if result["proxy"]:
                    break
                time.sleep(1)
            proxy = observed(runtime, ["get", "daemonset", "kube-proxy", "-n", "kube-system"])
            proxy_ready = proxy.get("status", {}).get("numberReady", 0)
            result["proxy"] = result["proxy"] and proxy_ready == len(runtime.discover())
            details["dns"] = {"fresh_service_name_resolves": result["dns"]}
            details["proxy"] = {
                "fresh_service_cluster_ip_reachable": result["proxy"],
                "ready_proxy_agents": proxy_ready,
            }
    finally:
        if created:
            removed = runtime.kubectl(["delete", "service", name, "--wait=true"], timeout=20)
            if not removed.ok:
                result["dns"] = result["proxy"] = False
    with suppress(*ERRORS):
        baseline = json.loads((runtime.root / "data/maintenance-baseline.json").read_text())
        claim = observed(runtime, ["get", "pvc", "data-db-0"])
        volume = observed(runtime, ["get", "pv", claim["spec"]["volumeName"]])
        database = observed(runtime, ["get", "pod", "db-0"])
        node = "lima-d" + runtime.lab.id[:10] + "-worker"
        registration = observed(runtime, ["get", "csinode", node])
        attachments = observed(runtime, ["get", "volumeattachments"])["items"]
        mounted = runtime.kubectl(
            [
                "exec",
                "statefulset/db",
                "--",
                "sh",
                "-c",
                'test -r "$PGDATA/PG_VERSION" && test -w "$PGDATA"',
            ],
            timeout=20,
        )
        result["csi"] = bool(
            claim["metadata"]["uid"] == baseline["storage"]["claim_uid"]
            and volume["metadata"]["uid"] == baseline["storage"]["volume_uid"]
            and volume["spec"]["csi"]["driver"] == "hostpath.csi.k8s.io"
            and volume["spec"]["csi"]["volumeHandle"] == baseline["storage"]["handle"]
            and database["spec"]["nodeName"] == node
            and any(
                driver["name"] == "hostpath.csi.k8s.io"
                for driver in registration["spec"]["drivers"]
            )
            and any(
                a["spec"]["source"].get("persistentVolumeName") == volume["metadata"]["name"]
                and a.get("status", {}).get("attached")
                for a in attachments
            )
            and mounted.ok
        )
        details["csi"] = {
            "driver": volume["spec"].get("csi", {}).get("driver"),
            "database_node": database["spec"].get("nodeName"),
            "original_volume": volume["metadata"]["uid"] == baseline["storage"]["volume_uid"],
            "database_mount_readable_and_writable": mounted.ok,
        }
    return result


if __name__ == "__main__":
    print(json.dumps(infrastructure()))
