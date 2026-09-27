"""Resume only after previously healthy native capabilities have returned."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from dockyard.runtimes.docker import RuntimeErrorBase

if TYPE_CHECKING:
    from dockyard.runtimes.linux import LinuxRuntime


def record(runtime: LinuxRuntime, cancel: threading.Event) -> None:
    contract: dict[str, Any] = {}
    with suppress(OSError, ValueError, KeyError):
        contract["application"] = application_ready(runtime)
    if runtime.lab.resources.get("kubeconfig_identity"):
        with suppress(RuntimeError, ValueError, KeyError):
            ready = runtime.kubectl(
                ["get", "--raw=/readyz", "--request-timeout=2s"], timeout=5, cancel=cancel
            )
            if ready.ok:
                contract["api"] = True
                contract["scheduling"] = False
                for entry in runtime.discover():
                    if "-cp" in entry["name"]:
                        scheduler = runtime.guest(
                            entry["name"],
                            ["sudo", "crictl", "ps", "--name", "^kube-scheduler$", "-q"],
                            cancel=cancel,
                        )
                        if scheduler.ok and scheduler.stdout.strip():
                            contract["scheduling"] = True
                observed = runtime.kubectl(
                    ["get", "nodes", "-o", "json", "--request-timeout=3s"], timeout=6, cancel=cancel
                )
                runtime.require(observed)
                contract["nodes"] = [
                    n["metadata"]["name"]
                    for n in json.loads(observed.stdout)["items"]
                    if any(
                        c["type"] == "Ready" and c["status"] == "True"
                        for c in n["status"]["conditions"]
                    )
                ]
                workloads = runtime.kubectl(
                    ["get", "deployments", "-A", "-o", "json", "--request-timeout=3s"],
                    timeout=6,
                    cancel=cancel,
                )
                runtime.require(workloads)
                contract["workloads"] = [
                    {
                        "namespace": d["metadata"]["namespace"],
                        "name": d["metadata"]["name"],
                        "uid": d["metadata"]["uid"],
                        "replicas": d["spec"].get("replicas", 1),
                    }
                    for d in json.loads(workloads.stdout)["items"]
                    if d["spec"].get("replicas", 1) > 0
                    and d.get("status", {}).get("availableReplicas", 0)
                    >= d["spec"].get("replicas", 1)
                    and d.get("status", {}).get("observedGeneration") == d["metadata"]["generation"]
                ]
    runtime.lab.resources["resume_contract"] = json.dumps(contract)
    runtime.save(runtime.lab)


def wait(runtime: LinuxRuntime, cancel: threading.Event) -> None:
    contract = json.loads(runtime.lab.resources.get("resume_contract", "{}"))
    if not contract.get("api"):
        return
    runtime.lab.resources["stage"] = (
        "Waiting for the previously healthy API, nodes, and workloads to resume"
    )
    runtime.save(runtime.lab)
    name = "dockyard-resume-" + uuid.uuid4().hex[:12]
    created = False
    resumed_at = datetime.now(UTC)
    deadline = time.monotonic() + 180
    try:
        while time.monotonic() < deadline:
            if cancel.is_set():
                raise RuntimeErrorBase("Resume readiness was canceled; the guests remain owned.")
            try:
                ready = runtime.kubectl(
                    ["get", "--raw=/readyz", "--request-timeout=3s"], timeout=6, cancel=cancel
                )
                runtime.require(ready)
                nodes = runtime.kubectl(
                    ["get", "nodes", "-o", "json", "--request-timeout=3s"], timeout=6, cancel=cancel
                )
                runtime.require(nodes)
                ready_nodes = {
                    n["metadata"]["name"]
                    for n in json.loads(nodes.stdout)["items"]
                    if any(
                        c["type"] == "Ready" and c["status"] == "True"
                        for c in n["status"]["conditions"]
                    )
                }
                if not set(contract.get("nodes", [])) <= ready_nodes:
                    raise RuntimeErrorBase("Previously ready nodes are still starting.")
                workloads = runtime.kubectl(
                    ["get", "deployments", "-A", "-o", "json", "--request-timeout=3s"],
                    timeout=6,
                    cancel=cancel,
                )
                runtime.require(workloads)
                items = {d["metadata"]["uid"]: d for d in json.loads(workloads.stdout)["items"]}
                for previous in contract.get("workloads", []):
                    actual = items.get(previous["uid"], {})
                    if actual.get("status", {}).get("availableReplicas", 0) < previous["replicas"]:
                        raise RuntimeErrorBase("Previously available workloads are still starting.")
                leases = runtime.kubectl(
                    ["get", "leases", "-n", "kube-node-lease", "-o", "json"],
                    timeout=6,
                    cancel=cancel,
                )
                runtime.require(leases)
                renewed = {
                    item["metadata"]["name"]
                    for item in json.loads(leases.stdout)["items"]
                    if datetime.fromisoformat(item["spec"]["renewTime"].replace("Z", "+00:00"))
                    > resumed_at
                }
                if not set(contract.get("nodes", [])) <= renewed:
                    raise RuntimeErrorBase("Waiting for fresh node-agent heartbeats.")
                if contract.get("application") and not application_ready(runtime):
                    raise RuntimeErrorBase("The previously healthy application is still starting.")
                # A real new assignment avoids mistaking persisted Ready conditions
                # for a functioning scheduler after the guests restart.
                source = next(
                    (
                        d
                        for d in items.values()
                        if d["metadata"]["namespace"] == "kube-system"
                        and d["metadata"]["name"] == "coredns"
                    ),
                    None,
                )
                if source and contract.get("scheduling"):
                    pod = {
                        "apiVersion": "v1",
                        "kind": "Pod",
                        "metadata": {"name": name, "namespace": "kube-system"},
                        "spec": source["spec"]["template"]["spec"],
                    }
                    pod["spec"].pop("nodeName", None)
                    pod["spec"]["terminationGracePeriodSeconds"] = 0
                    created = True
                    applied = runtime.kubectl(
                        ["apply", "-f", "-", "--request-timeout=3s"],
                        payload=json.dumps(pod),
                        timeout=6,
                        cancel=cancel,
                    )
                    runtime.require(applied)
                    created = True
                    assigned = runtime.kubectl(
                        [
                            "get",
                            "pod",
                            name,
                            "-n",
                            "kube-system",
                            "-o",
                            "json",
                            "--request-timeout=3s",
                        ],
                        timeout=6,
                        cancel=cancel,
                    )
                    runtime.require(assigned)
                    if not json.loads(assigned.stdout)["spec"].get("nodeName"):
                        raise RuntimeErrorBase("Waiting for a fresh scheduler assignment.")
                return
            except (RuntimeError, ValueError, KeyError, OSError):
                if cancel.wait(2):
                    raise RuntimeErrorBase("Resume readiness was canceled.") from None
        raise RuntimeErrorBase(
            "The guests started, but previously healthy cluster capabilities did not return "
            "within three minutes. Inspect this lab's API, node agents, and workload status "
            "before checking work."
        )
    finally:
        if created:
            runtime.kubectl(
                [
                    "delete",
                    "pod",
                    name,
                    "-n",
                    "kube-system",
                    "--ignore-not-found",
                    "--wait=true",
                    "--timeout=20s",
                ],
                timeout=25,
            )


def application_ready(runtime: LinuxRuntime) -> bool:
    port = int(runtime.env["DOCKYARD_PORT"])
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(f"http://127.0.0.1:{port}/readyz", timeout=2) as response:
        return bool(response.status == 200 and json.load(response).get("ready") is True)
