"""Distinct node-configuration and accidental control-plane deletion incidents."""

from __future__ import annotations

import json
import sys
import time

from dockyard.fixtures.maintenance import record
from dockyard.fixtures.recovery import snapshot
from dockyard.native import current
from dockyard.probes.maintenance import observed
from dockyard.workspace import atomic_write


def prepare(mode: str) -> None:
    r = current()
    primary = "d" + r.lab.id[:10] + "-cp1"
    worker = "d" + r.lab.id[:10] + "-worker"
    record()
    r.require(r.guest(primary, ["sudo", "mkdir", "-p", "/var/lib/dockyard"]))
    if mode == "deleted-state":
        frontend = observed(r, ["get", "deployment", "trusted-client", "-n", "frontend"])
        atomic_write(
            r.root / "data/incident-deployment.json",
            json.dumps({"uid": frontend["metadata"]["uid"]}).encode(),
        )
        snapshot(r)
        r.require(
            r.kubectl(
                [
                    "delete",
                    "deployment",
                    "trusted-client",
                    "-n",
                    "frontend",
                    "--wait=true",
                    "--timeout=60s",
                ],
                timeout=70,
            )
        )
        r.require(r.kubectl(["delete", "configmap", "maintenance-sentinel", "-n", "default"]))
    elif mode == "kubelet":
        r.require(r.guest(worker, ["sudo", "mkdir", "-p", "/var/lib/dockyard"]))
        r.require(
            r.guest(
                worker,
                [
                    "sudo",
                    "python3",
                    "-c",
                    """
from pathlib import Path
import re
p = Path('/var/lib/kubelet/config.yaml')
s = p.read_text()
Path('/var/lib/dockyard/kubelet-before-incident.yaml').write_text(s)
changed, count = re.subn(
    r'^shutdownGracePeriod:.*$', 'shutdownGracePeriod: invalid-duration', s, flags=re.M
)
assert count == 1
p.write_text(changed)
""",
                ],
            )
        )
        r.require(r.guest(worker, ["sudo", "systemctl", "restart", "kubelet"]))
        deadline = time.monotonic() + 100
        while time.monotonic() < deadline:
            node = observed(r, ["get", "node", "lima-" + worker])
            if any(
                c["type"] == "Ready" and c["status"] != "True" for c in node["status"]["conditions"]
            ):
                break
            time.sleep(2)
        else:
            raise RuntimeError("The kubelet incident did not produce a real NotReady node.")
    else:
        raise ValueError("Unknown native incident.")
    print("Prepared the owned incident and retained the original recovery evidence.")


if __name__ == "__main__":
    prepare(sys.argv[1])
