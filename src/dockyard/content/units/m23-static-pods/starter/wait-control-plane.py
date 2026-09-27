import json
import time
import uuid

import yaml

from dockyard.native import current

r = current()
name = "dockyard-recovery-wait-" + uuid.uuid4().hex[:10]
deadline = time.monotonic() + 240
created = False
try:
    while time.monotonic() < deadline:
        # A previously healthy API can answer once before etcd restarts.
        # Retry the complete read, write, and scheduling observation instead.
        source = r.kubectl(
            [
                "get",
                "deployment",
                "trusted-client",
                "-n",
                "frontend",
                "-o",
                "json",
                "--request-timeout=3s",
            ],
            timeout=6,
        )
        if source.ok:
            spec = json.loads(source.stdout)["spec"]["template"]["spec"]
            spec.pop("nodeName", None)
            spec["terminationGracePeriodSeconds"] = 0
            pod = {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {"name": name, "namespace": "frontend"},
                "spec": spec,
            }
            result = r.kubectl(
                ["apply", "-f", "-", "--request-timeout=3s"],
                payload=yaml.safe_dump(pod),
                timeout=6,
            )
            created = created or result.ok
            if result.ok:
                assigned = r.kubectl(
                    ["get", "pod", name, "-n", "frontend", "-o", "json", "--request-timeout=3s"],
                    timeout=6,
                )
                if assigned.ok and json.loads(assigned.stdout).get("spec", {}).get("nodeName"):
                    break
        time.sleep(2)
    else:
        raise RuntimeError(
            "The private control plane did not complete a fresh scheduler assignment within four minutes."
        )
finally:
    # The API may have accepted a write even if its response timed out.
    cleanup = r.kubectl(
        [
            "delete",
            "pod",
            name,
            "-n",
            "frontend",
            "--ignore-not-found",
            "--wait=true",
            "--timeout=30s",
        ],
        timeout=35,
    )
    if created:
        r.require(cleanup)
print("A fresh scheduler assignment confirms useful control-plane recovery.")
