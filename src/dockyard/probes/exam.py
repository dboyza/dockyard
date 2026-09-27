"""Original performance-task observations, reused by timed and untimed assessment."""

from __future__ import annotations

import json
import sys
import time
import uuid
from contextlib import suppress
from typing import Any

from dockyard.probes.incident import archive, observe
from dockyard.probes.kubernetes import get, kubectl, owned_pods
from dockyard.probes.releases import request
from dockyard.probes.security import connections

ERRORS = (RuntimeError, ValueError, KeyError, OSError, IndexError, StopIteration, TypeError)


def sidecar() -> bool:
    with suppress(*ERRORS):
        pod = get("pod", "audit-tail")
        spec = pod["spec"]
        containers = {c["name"]: c for c in spec["containers"]}
        init = next(c for c in spec.get("initContainers", []) if c["name"] == "seed")
        mounts = [
            next(m["name"] for m in c.get("volumeMounts", []) if m["mountPath"] == "/shared")
            for c in (init, containers["producer"], containers["tailer"])
        ]
        if len(set(mounts)) != 1 or not any(
            v["name"] == mounts[0] and "emptyDir" in v for v in spec["volumes"]
        ):
            return False
        if not any(
            s["name"] == "seed" and s.get("state", {}).get("terminated", {}).get("exitCode") == 0
            for s in pod["status"].get("initContainerStatuses", [])
        ):
            return False
        marker = "assessment-" + uuid.uuid4().hex
        kubectl(
            "exec",
            "audit-tail",
            "-c",
            "producer",
            "--",
            "python",
            "-c",
            "from pathlib import Path; p=Path('/shared/events'); "
            f"p.write_text(p.read_text()+{marker!r}+'\\n')",
        )
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            logs = kubectl("logs", "audit-tail", "-c", "tailer", "--tail=100")
            if "release audit ready" in logs and "dispatch-exam-a" in logs and marker in logs:
                return True
            time.sleep(0.5)
    return False


def ckad_a() -> dict[str, Any]:
    result = observe("exam")
    result.update(
        dict.fromkeys(("image", "configuration", "probes", "schedule", "sidecar", "network"), False)
    )
    with suppress(*ERRORS):
        _, pods = owned_pods("dispatch")
        result["image"] = len(pods) == 2 and all(
            request(p["metadata"]["name"], "127.0.0.1").get("release") == "dispatch-exam-a"
            and int(kubectl("exec", p["metadata"]["name"], "-c", "api", "--", "id", "-u")) != 0
            for p in pods
        )
        configured = [request(p["metadata"]["name"], "127.0.0.1", "/config") for p in pods]
        result["configuration"] = len(configured) == 2 and all(
            c.get("environment") == "assessment" and c.get("banner") == "Dispatch release accepted"
            for c in configured
        )
        probe_contract = []
        for pod in pods:
            api = next(c for c in pod["spec"]["containers"] if c["name"] == "api")
            startup = api.get("startupProbe", {})
            probe_contract.append(
                all(
                    api.get(kind, {}).get("httpGet", {}).get("path") == path
                    for kind, path in (
                        ("startupProbe", "/startupz"),
                        ("livenessProbe", "/healthz"),
                        ("readinessProbe", "/readyz"),
                    )
                )
                and startup.get("failureThreshold", 3) * startup.get("periodSeconds", 10) >= 30
                and request(pod["metadata"]["name"], "127.0.0.1", "/readyz").get("ready") is True
            )
        result["probes"] = len(probe_contract) == 2 and all(probe_contract)
    with suppress(*ERRORS):
        cron = get("cronjob", "release-audit")
        proof = get("job", "release-audit-proof")
        succeeded = [
            pod
            for pod in get("pods")["items"]
            if pod.get("status", {}).get("phase") == "Succeeded"
            and any(
                owner["uid"] == proof["metadata"]["uid"]
                for owner in pod["metadata"].get("ownerReferences", [])
            )
        ]
        result["schedule"] = (
            cron["spec"]["schedule"] == "17 2 * * *"
            and cron["spec"].get("timeZone") in {"UTC", "Etc/UTC"}
            and not cron["spec"].get("suspend", False)
            and cron["spec"].get("concurrencyPolicy") == "Forbid"
            and any(
                c["type"] == "Complete" and c["status"] == "True"
                for c in proof.get("status", {}).get("conditions", [])
            )
            and any(
                owner["uid"] == cron["metadata"]["uid"]
                for owner in proof["metadata"].get("ownerReferences", [])
            )
            and any(
                json.loads(kubectl("logs", pod["metadata"]["name"]))["release"] == "dispatch-exam-a"
                for pod in succeeded
            )
        )
    result["storage"] = archive("reports", "reporter")
    result["sidecar"] = sidecar()
    with suppress(*ERRORS):
        _, targets = owned_pods("audit-target")
        target = targets[0]["status"]["podIP"]
        result["network"] = connections("audit-reader", "dispatch", [(target, 8080)]) == [
            True
        ] and connections("audit-outsider", "dispatch", [(target, 8080)]) == [False]
    return result


if __name__ == "__main__":
    if sys.argv[1:] != ["ckad-a"]:
        raise SystemExit("Unknown authored exam observation.")
    print(json.dumps(ckad_a()))
