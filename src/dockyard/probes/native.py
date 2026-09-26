"""Observe native CRI processes, kubelet heartbeats, guest credentials, and real jobs."""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.request
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from dockyard.native import current
from dockyard.probes.kubernetes import get, owned_pods, sql
from dockyard.probes.security import request


def workflow() -> bool:
    job_id = None
    try:
        port = int(os.environ["DOCKYARD_PORT"])
        browser = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with browser.open(f"http://127.0.0.1:{port}/readyz", timeout=3) as response:
            if response.status != 200 or json.load(response).get("ready") is not True:
                return False
        title = "native-" + uuid.uuid4().hex
        job_id = request("/jobs", {"title": title}, "POST")["id"]
        if (
            not isinstance(job_id, str)
            or len(job_id) != 32
            or any(c not in "0123456789abcdef" for c in job_id)
        ):
            return False
        _, workers = owned_pods("worker")
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            rows = request("/jobs")["jobs"]
            visible = next((row for row in rows if row["id"] == job_id), None)
            row = json.loads(
                sql(
                    f"SELECT row_to_json(j) FROM jobs j WHERE id='{job_id}'",
                    workload="statefulset/db",
                )
            )
            if visible and visible["status"] == "done" and row["status"] == "done":
                return bool(
                    row["title"] == title
                    and row["result"]
                    == {
                        "normalized": title.upper(),
                        "sha256": hashlib.sha256(title.encode()).hexdigest(),
                    }
                    and row["worker"] in {pod["metadata"]["name"] for pod in workers}
                )
            time.sleep(0.3)
        return False
    finally:
        if (
            isinstance(job_id, str)
            and len(job_id) == 32
            and all(c in "0123456789abcdef" for c in job_id)
        ):
            with suppress(RuntimeError):
                sql(f"DELETE FROM jobs WHERE id='{job_id}'", workload="statefulset/db")


def internals() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(("cri", "kubelet", "operator", "workflow"), False)
    details: dict[str, Any] = {}
    result["_details"] = details
    runtime = current()
    names = [entry["name"] for entry in runtime.discover()]
    primary, worker = names[0], names[-1]
    errors = (RuntimeError, ValueError, KeyError, OSError, IndexError, StopIteration)
    with suppress(*errors):
        info = runtime.guest(worker, ["sudo", "crictl", "info"], timeout=20)
        actual = json.loads(info.stdout)
        conditions = actual["status"]["conditions"]
        systemd = actual["config"]["containerd"]["runtimes"]["runc"]["options"]["SystemdCgroup"]
        containers = runtime.guest(worker, ["sudo", "crictl", "ps", "-o", "json"], timeout=20)
        api = next(
            container
            for container in json.loads(containers.stdout)["containers"]
            if container.get("labels", {}).get("io.kubernetes.container.name") == "api"
            and container.get("labels", {}).get("io.kubernetes.pod.namespace") == "dispatch"
        )
        inspected = runtime.guest(worker, ["sudo", "crictl", "inspect", api["id"]], timeout=20)
        pid = int(json.loads(inspected.stdout)["info"]["pid"])
        if pid <= 1:
            raise ValueError("No actual workload process")
        cgroup = runtime.guest(worker, ["sudo", "cat", f"/proc/{pid}/cgroup"])
        result["cri"] = bool(
            info.ok
            and systemd is True
            and any(item["type"] == "RuntimeReady" and item["status"] for item in conditions)
            and cgroup.ok
            and "kubepods.slice" in cgroup.stdout
        )
        details["cri"] = {
            "runtime_ready": any(
                item["type"] == "RuntimeReady" and item["status"] for item in conditions
            ),
            "systemd_cgroups": systemd,
            "api_process_pid": pid,
            "api_in_kubepods_slice": "kubepods.slice" in cgroup.stdout,
        }
    with suppress(*errors):
        nodes = get("nodes")["items"]
        leases = get("leases", namespace="kube-node-lease")["items"]
        expected = {"lima-" + name for name in names}
        current_leases = {
            lease["metadata"]["name"]: (
                datetime.now(UTC)
                - datetime.fromisoformat(lease["spec"]["renewTime"].replace("Z", "+00:00"))
            ).total_seconds()
            for lease in leases
        }
        active = {
            name: runtime.guest(name, ["systemctl", "is-active", "kubelet"]).stdout.strip()
            == "active"
            for name in names
        }
        ready = {
            node["metadata"]["name"]
            for node in nodes
            if any(
                item["type"] == "Ready" and item["status"] == "True"
                for item in node.get("status", {}).get("conditions", [])
            )
        }
        result["kubelet"] = (
            all(active.values())
            and expected <= ready
            and all(0 <= current_leases.get(name, 999) < 45 for name in expected)
        )
        details["kubelet"] = {
            "services_active": active,
            "ready_nodes": sorted(ready),
            "lease_age_seconds": {
                name: round(current_leases.get(name, 999)) for name in sorted(expected)
            },
        }
    with suppress(*errors):
        observed = runtime.guest(
            primary,
            [
                "sh",
                "-c",
                'kubectl --kubeconfig="$HOME/.kube/operator.conf" '
                "--request-timeout=5s get nodes -o json",
            ],
            timeout=15,
        )
        operator_nodes = {node["metadata"]["name"] for node in json.loads(observed.stdout)["items"]}
        mode = runtime.guest(primary, ["sh", "-c", 'stat -c %a "$HOME/.kube/operator.conf"'])
        configuration = runtime.guest(
            primary,
            [
                "sh",
                "-c",
                'kubectl --kubeconfig="$HOME/.kube/operator.conf" config view --minify -o json',
            ],
        )
        cluster = json.loads(configuration.stdout)["clusters"][0]["cluster"]
        trusted = (
            cluster.get("insecure-skip-tls-verify") is not True
            and cluster.get("server", "").startswith("https://")
            and bool(
                cluster.get("certificate-authority-data") or cluster.get("certificate-authority")
            )
        )
        certificate = runtime.guest(
            primary,
            [
                "sudo",
                "openssl",
                "verify",
                "-CAfile",
                "/etc/kubernetes/pki/ca.crt",
                "/etc/kubernetes/pki/apiserver.crt",
            ],
        )
        static = runtime.guest(primary, ["sudo", "crictl", "ps", "-o", "json"], timeout=20)
        components = {
            item.get("labels", {}).get("io.kubernetes.container.name")
            for item in json.loads(static.stdout)["containers"]
        }
        required = {"etcd", "kube-apiserver", "kube-controller-manager", "kube-scheduler"}
        result["operator"] = (
            observed.ok
            and operator_nodes == {"lima-" + name for name in names}
            and mode.stdout.strip() == "600"
            and trusted
            and certificate.ok
            and required <= components
        )
        details["operator"] = {
            "authenticated_node_count": len(operator_nodes),
            "private_mode": mode.stdout.strip(),
            "api_certificate_valid": certificate.ok,
            "client_requires_ca_trust": trusted,
            "running_static_components": sorted(components & required),
        }
    with suppress(*errors):
        result["workflow"] = workflow()
    return result


if __name__ == "__main__":
    print(json.dumps(internals()))
