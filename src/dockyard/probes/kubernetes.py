"""Observe application behavior through the actual Kubernetes API and Pod network."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from dockyard.process import run


def kubectl(*args: str, timeout: float = 15) -> str:
    result = run(["kubectl", "--request-timeout=10s", *args], timeout=timeout)
    if not result.ok:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def get(kind: str, name: str = "", namespace: str = "dispatch") -> dict[str, Any]:
    args = ["get", kind, "-n", namespace, "-o", "json"]
    if name:
        args.append(name)
    return dict(json.loads(kubectl(*args)))


def foundation() -> dict[str, Any]:
    deployment = get("deployment", "dispatch")
    replicasets = get("rs")["items"]
    pods = get("pods")["items"]
    service = get("svc", "dispatch")
    desired = deployment["spec"].get("replicas", 1)
    status = deployment.get("status", {})
    owned_rs = {
        rs["metadata"]["uid"]
        for rs in replicasets
        if any(
            owner["uid"] == deployment["metadata"]["uid"]
            for owner in rs["metadata"].get("ownerReferences", [])
        )
    }
    active = [
        pod
        for pod in pods
        if not pod["metadata"].get("deletionTimestamp")
        and any(owner["uid"] in owned_rs for owner in pod["metadata"].get("ownerReferences", []))
    ]
    output: dict[str, Any] = {
        "replicas": desired == 2
        and status.get("availableReplicas", 0) == 2
        and status.get("observedGeneration") == deployment["metadata"]["generation"],
        "owned_pods": len(active) == 2,
        "labels": len(active) == 2
        and all(pod["metadata"].get("labels", {}).get("app") == "dispatch" for pod in active),
        "response": False,
        "service": False,
        "source_api": yaml.safe_load(Path("deployment.yaml").read_text())["apiVersion"]
        == "apps/v1",
    }
    responses = []
    for pod in active:
        try:
            body = json.loads(
                kubectl(
                    "exec",
                    "-n",
                    "dispatch",
                    pod["metadata"]["name"],
                    "-c",
                    "api",
                    "--",
                    "python",
                    "-c",
                    "import urllib.request; "
                    "print(urllib.request.urlopen('http://127.0.0.1:8080/healthz',timeout=2)"
                    ".read().decode())",
                )
            )
            responses.append(
                body.get("service") == "dispatch"
                and body.get("release") == "dispatch-1"
                and body.get("hostname") == pod["metadata"]["name"]
            )
        except (RuntimeError, ValueError):
            responses.append(False)
    output["response"] = len(responses) == 2 and all(responses)
    selector = service["spec"].get("selector", {})
    if (
        active
        and selector
        and all(
            all(
                pod["metadata"].get("labels", {}).get(key) == value
                for key, value in selector.items()
            )
            for pod in active
        )
    ):
        try:
            body = json.loads(
                kubectl(
                    "exec",
                    "-n",
                    "dispatch",
                    active[0]["metadata"]["name"],
                    "-c",
                    "api",
                    "--",
                    "python",
                    "-c",
                    "import urllib.request; "
                    "print(urllib.request.urlopen('http://dispatch.dispatch.svc.cluster.local:8080"
                    "/healthz',timeout=3).read().decode())",
                )
            )
            output["service"] = body.get("service") == "dispatch" and body.get("hostname") in {
                pod["metadata"]["name"] for pod in active
            }
        except (RuntimeError, ValueError):
            pass
    return output


def owned_pods(name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    deployment = get("deployment", name)
    sets = {
        item["metadata"]["uid"]
        for item in get("rs")["items"]
        if any(
            owner["uid"] == deployment["metadata"]["uid"]
            for owner in item["metadata"].get("ownerReferences", [])
        )
    }
    pods = [
        pod
        for pod in get("pods")["items"]
        if not pod["metadata"].get("deletionTimestamp")
        and any(owner["uid"] in sets for owner in pod["metadata"].get("ownerReferences", []))
    ]
    return deployment, pods


def available(deployment: dict[str, Any], count: int) -> bool:
    status = deployment.get("status", {})
    return bool(
        deployment["spec"].get("replicas", 1) == count
        and status.get("availableReplicas", 0) == count
        and status.get("observedGeneration") == deployment["metadata"]["generation"]
    )


def sql(query: str) -> str:
    return kubectl(
        "exec",
        "-n",
        "dispatch",
        "deployment/db",
        "--",
        "psql",
        "-U",
        "dispatch",
        "-d",
        "dispatch",
        "-At",
        "-c",
        query,
    )


def api_request(
    path: str, payload: dict[str, Any] | None = None, method: str = "GET"
) -> dict[str, Any]:
    script = (
        "import json,urllib.request; "
        f"data={repr(json.dumps(payload).encode()) if payload is not None else 'None'}; "
        f"request=urllib.request.Request({'http://dispatch:8080' + path!r},data=data,"
        f"headers={{'Content-Type':'application/json'}},method={method!r}); "
        "print(urllib.request.urlopen(request,timeout=3).read().decode())"
    )
    return dict(
        json.loads(
            kubectl(
                "exec",
                "-n",
                "dispatch",
                "deployment/dispatch",
                "-c",
                "api",
                "--",
                "python",
                "-c",
                script,
            )
        )
    )


def workloads() -> dict[str, Any]:
    api, _ = owned_pods("dispatch")
    worker, pods = owned_pods("worker")
    result: dict[str, Any] = {
        "api": available(api, 2),
        "workers": available(worker, 2) and len(pods) == 2,
        "processing": False,
        "agents": False,
        "patterns": False,
        "schedule": False,
        "maintenance": False,
    }
    job_id = None
    try:
        title = "dockyard-observation-" + uuid.uuid4().hex
        job_id = str(api_request("/jobs", {"title": title}, "POST")["id"])
        if len(job_id) != 32 or not all(c in "0123456789abcdef" for c in job_id):
            raise ValueError("The API returned an invalid job identity.")
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            jobs = api_request("/jobs")["jobs"]
            current = next((item for item in jobs if item["id"] == job_id), None)
            if current and current["status"] == "done":
                stored = json.loads(sql(f"SELECT row_to_json(j) FROM jobs j WHERE id='{job_id}'"))
                result["processing"] = (
                    stored["title"] == title
                    and stored["status"] == "done"
                    and stored["result"]
                    == {
                        "normalized": title.upper(),
                        "sha256": hashlib.sha256(title.encode()).hexdigest(),
                    }
                    and stored["worker"] in {pod["metadata"]["name"] for pod in pods}
                    and current["result"] == stored["result"]
                )
                break
            time.sleep(0.3)
    except (RuntimeError, ValueError, KeyError):
        pass
    finally:
        if job_id and len(job_id) == 32 and all(c in "0123456789abcdef" for c in job_id):
            with suppress(RuntimeError):
                sql(f"DELETE FROM jobs WHERE id='{job_id}'")
    agent = get("daemonset", "dispatch-node-agent")
    status = agent.get("status", {})
    desired = status.get("desiredNumberScheduled", 0)
    agent_pods = [
        pod
        for pod in get("pods")["items"]
        if any(
            owner["uid"] == agent["metadata"]["uid"]
            for owner in pod["metadata"].get("ownerReferences", [])
        )
        and not pod["metadata"].get("deletionTimestamp")
    ]
    result["agents"] = (
        desired > 0 and status.get("numberReady") == desired and len(agent_pods) == desired
    )
    patterns = []
    for pod in pods:
        try:
            spec = pod["spec"]
            init = next(c for c in spec.get("initContainers", []) if c["name"] == "configure")
            containers = {c["name"]: c for c in spec["containers"]}
            mounts = [
                next(m["name"] for m in c.get("volumeMounts", []) if m["mountPath"] == "/shared")
                for c in (init, containers["worker"], containers["observer"])
            ]
            shared = len(set(mounts)) == 1 and any(
                volume["name"] == mounts[0] and "emptyDir" in volume
                for volume in spec.get("volumes", [])
            )
            completed = any(
                c["name"] == "configure"
                and c.get("state", {}).get("terminated", {}).get("exitCode") == 0
                for c in pod.get("status", {}).get("initContainerStatuses", [])
            )
            content = [
                kubectl(
                    "exec",
                    "-n",
                    "dispatch",
                    pod["metadata"]["name"],
                    "-c",
                    c,
                    "--",
                    "cat",
                    "/shared/worker.conf",
                )
                for c in ("worker", "observer")
            ]
            log = kubectl(
                "logs", "-n", "dispatch", pod["metadata"]["name"], "-c", "observer", "--tail=5"
            )
            patterns.append(
                shared
                and completed
                and content == ["queue=redis://queue:6379/0"] * 2
                and "queue=redis://queue:6379/0" in log
            )
        except (RuntimeError, KeyError, StopIteration):
            patterns.append(False)
    result["patterns"] = len(patterns) == 2 and all(patterns)
    cron = get("cronjob", "dispatch-maintenance")["spec"]
    template = cron["jobTemplate"]["spec"]
    result["schedule"] = (
        cron["schedule"] == "*/5 * * * *"
        and not cron.get("suspend", False)
        and cron.get("concurrencyPolicy") == "Forbid"
        and 0 <= template.get("backoffLimit", 6) <= 3
        and template["template"]["spec"].get("restartPolicy") in {"Never", "OnFailure"}
    )
    try:
        proof = get("job", "maintenance-proof")
        complete = any(
            c["type"] == "Complete" and c["status"] == "True"
            for c in proof.get("status", {}).get("conditions", [])
        )
        row = json.loads(
            sql("SELECT row_to_json(m) FROM maintenance_runs m WHERE name='maintenance-proof'")
        )
        result["maintenance"] = (
            complete
            and row["jobs"] >= 0
            and datetime.fromisoformat(row["observed_at"])
            >= datetime.fromisoformat(proof["metadata"]["creationTimestamp"].replace("Z", "+00:00"))
        )
    except (RuntimeError, ValueError, KeyError):
        pass
    return result


def main() -> None:
    if not os.environ.get("DOCKYARD_LAB") or not os.environ.get("KUBECONFIG"):
        raise SystemExit("Run this check inside a Dockyard practice environment.")
    probes = {"foundation": foundation, "workloads": workloads}
    try:
        result = probes[sys.argv[1]]()
    except (RuntimeError, ValueError, KeyError, IndexError, OSError) as error:
        print(json.dumps({"error": str(error)}))
        raise SystemExit(1) from error
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
