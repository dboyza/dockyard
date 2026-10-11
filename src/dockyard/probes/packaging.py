"""Observe packaging intent, Helm recovery, and real custom-resource reconciliation."""

from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any

import yaml

from dockyard.probes.kubernetes import api_request, available, get, kubectl, owned_pods
from dockyard.process import run

# How long a restored WorkerPool's Deployment may take to become available again.
WORKERS_SETTLE_SECONDS = 45


def helm(*args: str) -> Any:
    result = run(["helm", *args, "-n", "staging", "-o", "json"], timeout=30)
    if not result.ok:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def pool_ready(pool: dict[str, Any]) -> bool:
    """Whether the controller has observed the pool's current spec and reports it Ready."""
    generation = pool["metadata"]["generation"]
    status = pool.get("status", {})
    return status.get("observedGeneration") == generation and any(
        c["type"] == "Ready" and c["status"] == "True" and c.get("observedGeneration") == generation
        for c in status.get("conditions", [])
    )


def packaging() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(
        ("overlay", "release", "rollback", "extension", "reconciliation", "workers"), False
    )
    details: dict[str, Any] = {}
    result["_details"] = details
    with suppress(RuntimeError, ValueError, KeyError, OSError, StopIteration):
        rendered = list(yaml.safe_load_all(kubectl("kustomize", "kustomize/overlays/development")))
        desired = next(
            d for d in rendered if d["kind"] == "Deployment" and d["metadata"]["name"] == "dispatch"
        )
        config = next(
            d
            for d in rendered
            if d["kind"] == "ConfigMap" and d["metadata"]["name"] == "dispatch-settings"
        )
        live, pods = owned_pods("dispatch")
        environment = api_request("/config")["environment"]
        details["overlay"] = {
            "rendered_replicas": desired["spec"]["replicas"],
            "rendered_environment": config["data"]["environment"],
            "live_environment": environment,
            "available": live.get("status", {}).get("availableReplicas", 0),
        }
        result["overlay"] = (
            desired["metadata"]["namespace"] == config["metadata"]["namespace"] == "dispatch"
            and desired["spec"]["replicas"] == 2
            and config["data"]["environment"] == environment == "development"
            and get("cm", "dispatch-settings")["data"]["environment"] == "development"
            and available(live, 2)
            and len(pods) == 2
        )
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        history = helm("history", "dispatch")
        values = helm("get", "values", "dispatch")
        source = yaml.safe_load(Path("values-practice.yaml").read_text())
        live, pods = owned_pods("dispatch", "staging")
        details["release"] = {
            "history": history,
            "values": {"api": values.get("api"), "environment": values.get("environment")},
            "available": live.get("status", {}).get("availableReplicas", 0),
        }
        result["release"] = (
            history[-1]["status"] == "deployed"
            and values["api"]["replicas"] == source["api"]["replicas"] == 2
            and values["environment"] == source["environment"] == "staging"
            and available(live, 2)
            and len(pods) == 2
            and live["metadata"].get("annotations", {}).get("meta.helm.sh/release-name")
            == "dispatch"
            and api_request("/config", namespace="staging")["environment"] == "staging"
        )
        result["rollback"] = (
            result["release"]
            and len(history) >= 3
            and any(
                str(revision.get("description", "")).startswith("Rollback to ")
                for revision in history[2:]
            )
        )
    with suppress(RuntimeError, ValueError, KeyError, OSError, StopIteration):
        crd = get("crd", "workerpools.learning.dockyard.local")
        version = next(v for v in crd["spec"]["versions"] if v["name"] == "v1alpha1")
        schema = version["schema"]["openAPIV3Schema"]["properties"]["spec"]["properties"][
            "replicas"
        ]
        controller, _ = owned_pods("workerpool-controller")
        # After a learner's own scale-down test, the controller restores the replicas at
        # once, but the new Pods need a few seconds to become available, and the pool
        # reports Ready only once they are; observe both again until they settle.
        settle_until = time.monotonic() + WORKERS_SETTLE_SECONDS
        while True:
            pool = get("workerpool", "dispatch")
            managed, pods = owned_pods("dispatch-workers")
            if (
                available(managed, 2) and len(pods) == 2 and pool_ready(pool)
            ) or time.monotonic() >= settle_until:
                break
            time.sleep(1)
        uid = pool["metadata"]["uid"]
        result["extension"] = (
            crd["spec"]["scope"] == "Namespaced"
            and version["served"]
            and version["storage"]
            and "status" in version["subresources"]
            and schema["type"] == "integer"
            and schema["minimum"] == 0
            and schema["maximum"] == 4
            and pool["spec"]["replicas"] == 2
            and pool_ready(pool)
            and any(
                o["uid"] == uid and o.get("controller")
                for o in managed["metadata"].get("ownerReferences", [])
            )
            and available(controller, 1)
            and available(managed, 2)
            and len(pods) == 2
        )
        record = json.loads(Path("operator-evidence.json").read_text())
        details["reconciliation"] = record
        result["reconciliation"] = (
            result["extension"]
            and record["lab"] == os.environ["DOCKYARD_LAB"]
            and record["pool_uid"] == uid
            and record["deployment_uid"] == managed["metadata"]["uid"]
            and record["before_replicas"] == 2
            and record["perturbed_replicas"] == 0
            and record["after_replicas"] == 2
            and record["before_generation"]
            < record["perturbed_generation"]
            < record["after_generation"]
            <= managed["metadata"]["generation"]
            and 0 < record["elapsed_seconds"] <= 120
        )
        ordinary, ordinary_pods = owned_pods("worker")
        if not result["extension"] or not available(ordinary, 0) or ordinary_pods:
            return result
        title = "operator-proof-" + uuid.uuid4().hex[:16]
        job = api_request("/jobs", {"title": title}, "POST")
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                jobs = api_request("/jobs")["jobs"]
                observed: dict[str, Any] = next((j for j in jobs if j["id"] == job["id"]), {})
                if observed.get("status") == "done":
                    result["workers"] = observed.get("result", {}).get(
                        "normalized"
                    ) == title.upper() and observed.get("worker") in {
                        p["metadata"]["name"] for p in pods
                    }
                    break
                time.sleep(0.5)
        finally:
            api_request("/jobs/" + job["id"], method="DELETE")
    return result
