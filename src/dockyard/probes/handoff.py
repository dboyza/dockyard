"""Observe operating constraints, actual identity permissions, and useful HA behavior."""

from __future__ import annotations

import json
import sys
from contextlib import suppress
from typing import Any

from dockyard.native import current
from dockyard.probes.bootstrap import ERRORS, high_availability
from dockyard.probes.capacity import quantity
from dockyard.probes.maintenance import maintenance, observed
from dockyard.probes.security import execute


def handoff(mode: str) -> dict[str, Any]:
    result = maintenance("handoff")
    result.update(dict.fromkeys(("capacity", "identity", "rollout"), False))
    runtime = current()
    with suppress(*ERRORS):
        deployment = observed(runtime, ["get", "deployment", "dispatch"])
        spec = deployment["spec"]
        status = deployment.get("status", {})
        replicas = spec["replicas"]
        result["rollout"] = bool(
            status.get("observedGeneration", 0) >= deployment["metadata"]["generation"]
            and status.get("updatedReplicas", 0) == replicas
            and status.get("availableReplicas", 0) == replicas
            and status.get("replicas", 0) == replicas
            and replicas >= 1
        )
        budget = observed(runtime, ["get", "pdb", "dispatch-operations"])
        containers = spec["template"]["spec"]["containers"]
        requests = [c["resources"]["requests"] for c in containers]
        limits = [c["resources"]["limits"] for c in containers]
        selected = budget["spec"].get("selector", {}).get("matchLabels") == {
            "app": "dispatch",
            "track": "stable",
        }
        protected = (
            budget["spec"].get("minAvailable") in (1, "50%")
            or budget["spec"].get("maxUnavailable") == 1
        )
        result["capacity"] = bool(
            result["rollout"]
            and 2 <= replicas <= 4
            and selected
            and protected
            and sum(quantity(r["cpu"]) for r in requests) * replicas <= 1
            and sum(quantity(r["memory"]) for r in requests) * replicas <= 512 * 1024**2
            and sum(quantity(r["memory"]) for r in limits) * replicas <= 1024**3
            and all(quantity(r["cpu"]) > 0 and quantity(r["memory"]) > 0 for r in requests)
            and all(
                quantity(c["resources"]["limits"][key]) >= quantity(c["resources"]["requests"][key])
                for c in containers
                for key in ("cpu", "memory")
            )
        )
        result["_details"]["capacity"] = {
            "available_api_replicas": status.get("availableReplicas", 0),
            "converged_rollout": result["rollout"],
            "budget_protects_one": selected and protected,
        }
    if mode in {"decisions", "mission"}:
        with suppress(*ERRORS):
            authorization = execute(
                "inventory",
                """import json,ssl,urllib.request,urllib.error
from pathlib import Path
base=Path('/var/run/secrets/kubernetes.io/serviceaccount')
context=ssl.create_default_context(cafile=str(base/'ca.crt'))
headers={'Authorization':'Bearer '+(base/'token').read_text()}
result={}
for name,path in [
    ('pods','/api/v1/namespaces/dispatch/pods'),
    ('secrets','/api/v1/namespaces/dispatch/secrets'),
    ('outside','/api/v1/namespaces/kube-system/pods'),
]:
    request=urllib.request.Request('https://kubernetes.default.svc'+path,headers=headers)
    try:
        with urllib.request.urlopen(request,context=context,timeout=3) as response:
            result[name]=response.status
    except urllib.error.HTTPError as error: result[name]=error.code; error.close()
print(json.dumps(result))
""",
            )
            writes = []
            for verb, resource in (
                ("create", "pods"),
                ("patch", "deployments"),
                ("create", "rolebindings"),
            ):
                answer = runtime.kubectl(
                    [
                        "auth",
                        "can-i",
                        verb,
                        resource,
                        "--as=system:serviceaccount:dispatch:dispatch-reader",
                    ]
                )
                writes.append(answer.stdout.strip())
            result["identity"] = (
                authorization == {"pods": 200, "secrets": 403, "outside": 403}
                and writes == ["no"] * 3
            )
            result["_details"]["identity"] = authorization
    if mode == "mission":
        result["release"] = False
        with suppress(*ERRORS):
            pods = observed(runtime, ["get", "pods", "-l", "app in (dispatch,worker)"])["items"]
            active = [p for p in pods if not p["metadata"].get("deletionTimestamp")]
            versions = []
            for pod in active:
                actual = runtime.kubectl(
                    [
                        "exec",
                        pod["metadata"]["name"],
                        "--",
                        "python",
                        "-c",
                        "from pathlib import Path; print(Path('/app/VERSION').read_text().strip())",
                    ]
                )
                versions.append(actual.ok and actual.stdout.strip() == "dispatch-handoff-v1")
            result["release"] = bool(
                len(active) >= 3
                and all(versions)
                and {p["metadata"]["labels"]["app"] for p in active} == {"dispatch", "worker"}
                and result["rollout"]
            )
        ha = high_availability()
        for key in ("outage", "quorum", "endpoint"):
            result[key] = ha[key]
            result["_details"][key] = ha["_details"].get(key, {})
    return result


if __name__ == "__main__":
    print(json.dumps(handoff(sys.argv[1])))
