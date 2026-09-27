"""Observe original object restoration and actual node-agent recovery."""

from __future__ import annotations

import json
import sys
from contextlib import suppress
from typing import Any

from dockyard.native import current
from dockyard.probes.bootstrap import ERRORS
from dockyard.probes.maintenance import observed
from dockyard.probes.recovery import recovery


def observe(mode: str) -> dict[str, Any]:
    r = current()
    result = recovery("etcd" if mode == "deleted-state" else "api")
    result["incident"] = False
    with suppress(*ERRORS):
        if mode == "deleted-state":
            original = json.loads((r.root / "data/incident-deployment.json").read_text())
            actual = observed(r, ["get", "deployment", "trusted-client", "-n", "frontend"])
            result["incident"] = (
                actual["metadata"]["uid"] == original["uid"]
                and actual.get("status", {}).get("availableReplicas", 0) >= 1
            )
        elif mode == "kubelet":
            worker = "d" + r.lab.id[:10] + "-worker"
            active = r.guest(worker, ["systemctl", "is-active", "kubelet"])
            nodes = observed(r, ["get", "nodes"])["items"]
            result["incident"] = (
                active.ok
                and len(nodes) == 2
                and all(
                    any(
                        c["type"] == "Ready" and c["status"] == "True"
                        for c in n["status"]["conditions"]
                    )
                    for n in nodes
                )
            )
    return result


if __name__ == "__main__":
    print(json.dumps(observe(sys.argv[1])))
