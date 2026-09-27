"""Observe independent maintenance outcomes without crediting unavailable infrastructure."""

from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

from dockyard.native import current
from dockyard.probes.bootstrap import ERRORS
from dockyard.probes.kubernetes import available, get, owned_pods
from dockyard.probes.maintenance import certificate, maintenance, served_serial
from dockyard.probes.recovery import recovery
from dockyard.probes.releases import endpoints
from dockyard.probes.security import connections, request, security


def maintenance_exam() -> dict[str, Any]:
    r = current()
    result = maintenance("upgrade")
    result.update(
        dict.fromkeys(("renewed", "scheduler", "rbac", "service", "network", "budget"), False)
    )
    with suppress(*ERRORS):
        baseline = json.loads((r.root / "data/maintenance-baseline.json").read_text())
        serial, ca = certificate(r)
        result["renewed"] = (
            serial != baseline["serial"] and served_serial(r) == serial and ca == baseline["ca"]
        )
    with suppress(*ERRORS):
        control = recovery("api")
        result["scheduler"] = control["components"] and control["scheduled"]
    with suppress(*ERRORS):

        def can(verb: str, resource: str) -> bool:
            return (
                r.kubectl(
                    [
                        "auth",
                        "can-i",
                        verb,
                        resource,
                        "-n",
                        "dispatch",
                        "--as=system:serviceaccount:dispatch:release-operator",
                    ]
                ).stdout.strip()
                == "yes"
            )

        result["rbac"] = all(
            can(v, x)
            for v, x in [
                ("get", "deployments.apps"),
                ("list", "deployments.apps"),
                ("get", "deployments.apps/scale"),
                ("patch", "deployments.apps/scale"),
                ("update", "deployments.apps/scale"),
            ]
        ) and not any(
            can(v, x)
            for v, x in [("get", "secrets"), ("create", "pods"), ("delete", "deployments.apps")]
        )
    with suppress(*ERRORS):
        d, pods = owned_pods("dispatch")
        result["service"] = (
            available(d, 2)
            and len(pods) == 2
            and endpoints("dispatch") == {p["metadata"]["uid"] for p in pods}
            and request("/healthz").get("service") == "dispatch"
        )
        pdb = get("pdb", "dispatch-maintenance")
        spec = pdb["spec"]
        selector = spec.get("selector", {}).get("matchLabels", {})
        selected = bool(selector) and all(
            all(p["metadata"].get("labels", {}).get(k) == v for k, v in selector.items())
            for p in pods
        )
        result["budget"] = (
            available(d, 2)
            and selected
            and (spec.get("minAvailable") in (1, "50%") or spec.get("maxUnavailable") in (1, "50%"))
            and pdb.get("status", {}).get("disruptionsAllowed") == 1
        )
    with suppress(*ERRORS):
        matrix = security()
        result["network"] = (
            matrix["network"]
            and matrix["dns"]
            and connections("dispatch", "dispatch", [("queue", 6379)]) == [True]
        )
    return result


if __name__ == "__main__":
    print(json.dumps(maintenance_exam()))
