"""Observe cgroups, admission, placement, metrics-driven scaling, and drain evidence."""

from __future__ import annotations

import json
import os
import uuid
from collections import Counter
from contextlib import suppress
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from dockyard.probes.kubernetes import api_request, available, get, kubectl, owned_pods
from dockyard.process import run


def quantity(value: Any) -> Decimal:
    text = str(value)
    multipliers: dict[str, int | Decimal] = {
        "Ki": 1024,
        "Mi": 1024**2,
        "Gi": 1024**3,
        "Ti": 1024**4,
        "n": Decimal("0.000000001"),
        "u": Decimal("0.000001"),
        "m": Decimal("0.001"),
        "k": 1000,
        "M": 1000**2,
        "G": 1000**3,
        "T": 1000**4,
    }
    for suffix, factor in multipliers.items():
        if text.endswith(suffix):
            return Decimal(text[: -len(suffix)]) * factor
    return Decimal(text)


def budget() -> bool:
    with suppress(RuntimeError, ValueError, KeyError):
        get("limitrange", "dispatch-defaults")
        quota = get("resourcequota", "dispatch-budget")
        if not 0 < quantity(quota["spec"]["hard"]["requests.cpu"]) <= 2:
            return False
        pod: dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "admission-proof-" + uuid.uuid4().hex[:12],
                "namespace": "dispatch",
            },
            "spec": {
                "restartPolicy": "Never",
                "containers": [
                    {
                        "name": "client",
                        "image": os.environ["DOCKYARD_BUSYBOX_LOCAL_IMAGE"],
                        "command": ["true"],
                    }
                ],
            },
        }
        observed = run(
            ["kubectl", "create", "--dry-run=server", "-f", "-", "-o", "json"],
            input_text=json.dumps(pod),
            timeout=20,
        )
        if not observed.ok:
            return False
        resources = json.loads(observed.stdout)["spec"]["containers"][0]["resources"]
        defaults = all(
            quantity(resources[kind][key]) > 0
            for kind in ("requests", "limits")
            for key in ("cpu", "memory")
        )
        pod["spec"]["containers"][0]["resources"] = {
            "requests": {"cpu": "3", "memory": "64Mi"},
            "limits": {"cpu": "3", "memory": "256Mi"},
        }
        denied = run(
            ["kubectl", "create", "--dry-run=server", "-f", "-"],
            input_text=json.dumps(pod),
            timeout=20,
        )
        return defaults and not denied.ok and "exceeded quota" in denied.stderr.lower()
    return False


def capacity() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(
        ("resources", "budget", "placement", "scaling", "disruption", "drain"), False
    )
    details: dict[str, Any] = {}
    result["_details"] = details
    deployment, pods = owned_pods("dispatch")
    count = deployment["spec"].get("replicas", 1)
    result["budget"] = budget()
    with suppress(RuntimeError, ValueError, KeyError, StopIteration):
        checks = []
        for pod in pods:
            api = next(c for c in pod["spec"]["containers"] if c["name"] == "api")
            limits, requests = api["resources"]["limits"], api["resources"]["requests"]
            memory = int(
                kubectl(
                    "exec",
                    pod["metadata"]["name"],
                    "-c",
                    "api",
                    "--",
                    "cat",
                    "/sys/fs/cgroup/memory.max",
                )
            )
            cpu = kubectl(
                "exec", pod["metadata"]["name"], "-c", "api", "--", "cat", "/sys/fs/cgroup/cpu.max"
            ).split()
            checks.append(
                Decimal("0.025") <= quantity(requests["cpu"]) <= Decimal("0.1")
                and 32 * 1024**2 <= quantity(requests["memory"]) <= 128 * 1024**2
                and quantity(requests["cpu"]) <= quantity(limits["cpu"]) <= 1
                and quantity(requests["memory"]) <= quantity(limits["memory"]) <= 512 * 1024**2
                and memory == quantity(limits["memory"])
                and Decimal(cpu[0]) / Decimal(cpu[1]) == quantity(limits["cpu"])
                and pod["status"].get("qosClass") == "Burstable"
            )
        result["resources"] = (
            len(checks) == count and count >= 2 and all(checks) and available(deployment, count)
        )
    nodes = get("nodes")["items"]
    pool = [n for n in nodes if n["metadata"].get("labels", {}).get("dockyard.pool") == "apps"]
    with suppress(RuntimeError, ValueError, KeyError):
        counts = Counter(p["spec"].get("nodeName") for p in pods)
        pool_names = {n["metadata"]["name"] for n in pool}
        tainted = all(
            any(
                t["key"] == "dockyard.pool"
                and t.get("value") == "apps"
                and t["effect"] == "NoSchedule"
                for t in n["spec"].get("taints", [])
            )
            for n in pool
        )
        spec = deployment["spec"]["template"]["spec"]
        terms = (
            spec.get("affinity", {})
            .get("nodeAffinity", {})
            .get("requiredDuringSchedulingIgnoredDuringExecution", {})
            .get("nodeSelectorTerms", [])
        )
        selects_pool = spec.get("nodeSelector", {}).get("dockyard.pool") == "apps" or (
            bool(terms)
            and all(
                any(
                    e["key"] == "dockyard.pool"
                    and e["operator"] == "In"
                    and e.get("values") == ["apps"]
                    for e in term.get("matchExpressions", [])
                )
                for term in terms
            )
        )
        spread = any(
            c.get("topologyKey") == "kubernetes.io/hostname"
            and c.get("maxSkew") == 1
            and c.get("whenUnsatisfiable") == "DoNotSchedule"
            for c in spec.get("topologySpreadConstraints", [])
        )
        result["placement"] = (
            result["resources"]
            and len(pool_names) == 2
            and tainted
            and selects_pool
            and spread
            and set(counts) == pool_names
            and max(counts.values()) - min(counts.values()) <= 1
        )
    with suppress(RuntimeError, ValueError, KeyError):
        hpa = get("hpa", "dispatch")
        spec, status = hpa["spec"], hpa.get("status", {})
        load, _ = owned_pods("practice-load")
        metrics = json.loads(
            kubectl("get", "--raw", "/apis/metrics.k8s.io/v1beta1/namespaces/dispatch/pods")
        )
        measured = {
            m["metadata"]["name"]
            for m in metrics["items"]
            if any(quantity(c["usage"]["cpu"]) > 0 for c in m["containers"])
        }
        target = spec["scaleTargetRef"]
        details["scaling"] = {
            "target": target,
            "hpa_status": status,
            "deployment": deployment.get("status", {}),
            "load_available": available(load, 1),
            "api_pods": sorted(p["metadata"]["name"] for p in pods),
            "measured_pods": sorted(measured),
        }
        cpu_metric = any(
            m.get("resource", {}).get("name") == "cpu"
            and m["resource"]["target"].get("averageUtilization") == 50
            for m in spec.get("metrics", [])
        )
        result["scaling"] = (
            target == {"apiVersion": "apps/v1", "kind": "Deployment", "name": "dispatch"}
            and spec["minReplicas"] == 2
            and spec["maxReplicas"] == 4
            and cpu_metric
            and status.get("currentReplicas") == status.get("desiredReplicas") == 4
            and any(
                c["type"] == "ScalingActive" and c["status"] == "True"
                for c in status.get("conditions", [])
            )
            and any(
                m.get("resource", {}).get("current", {}).get("averageUtilization", 0) > 50
                for m in status.get("currentMetrics", [])
            )
            and available(deployment, 4)
            and len(pods) == 4
            and available(load, 1)
            and {p["metadata"]["name"] for p in pods} <= measured
        )
    with suppress(RuntimeError, ValueError, KeyError):
        pdb = get("pdb", "dispatch")
        status = pdb.get("status", {})
        selector = pdb["spec"]["selector"].get("matchLabels", {})
        result["disruption"] = (
            bool(selector)
            and all(
                all(p["metadata"]["labels"].get(k) == v for k, v in selector.items()) for p in pods
            )
            and status.get("observedGeneration") == pdb["metadata"]["generation"]
            and status.get("desiredHealthy") == 2
            and status.get("currentHealthy", 0) >= 2
            and pdb["spec"].get("minAvailable") == 2
        )
    with suppress(OSError, RuntimeError, ValueError, KeyError, StopIteration):
        record = json.loads(Path("drain-evidence.json").read_text())
        details["drain"] = record
        node = next(n for n in pool if n["metadata"]["name"] == record["node"])
        start, finish = (
            datetime.fromisoformat(record["started_at"]),
            datetime.fromisoformat(record["finished_at"]),
        )
        created = datetime.fromisoformat(
            node["metadata"]["creationTimestamp"].replace("Z", "+00:00")
        )
        old = set(record["before_uids"])
        result["drain"] = (
            result["placement"]
            and result["scaling"]
            and result["disruption"]
            and record["lab"] == os.environ["DOCKYARD_LAB"]
            and record["samples"] >= 5
            and record["failures"] == 0
            and 3 <= (finish - start).total_seconds() <= 180
            and created <= start < finish <= datetime.now(UTC)
            and 1 <= len(old) <= 2
            and all(len(identity) == 36 for identity in old)
            and not old & {p["metadata"]["uid"] for p in pods}
            and not node["spec"].get("unschedulable", False)
            and api_request("/readyz").get("ready") is True
        )
    return result
