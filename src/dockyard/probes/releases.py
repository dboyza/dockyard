"""Observe rollout history, distinct release responses, and process termination."""

from __future__ import annotations

import json
import os
from contextlib import suppress
from typing import Any

from dockyard.probes.kubernetes import available, get, kubectl, owned_pods


def request(pod: str, destination: str, path: str = "/healthz") -> dict[str, Any]:
    script = (
        "import urllib.request; "
        f"print(urllib.request.urlopen({'http://' + destination + ':8080' + path!r},"
        "timeout=3).read().decode())"
    )
    return dict(json.loads(kubectl("exec", pod, "-c", "api", "--", "python", "-c", script)))


def endpoints(name: str) -> set[str]:
    return {
        endpoint.get("targetRef", {}).get("uid", "")
        for item in get("endpointslices")["items"]
        if item["metadata"].get("labels", {}).get("kubernetes.io/service-name") == name
        for endpoint in (item.get("endpoints") or [])
        if endpoint.get("conditions", {}).get("ready") is True
    }


def releases() -> dict[str, bool]:
    result = dict.fromkeys(
        ("available", "probes", "rollout", "history", "termination", "canary", "preview"), False
    )
    deployment, pods = owned_pods("dispatch")
    image = os.environ["DOCKYARD_IMAGE"]
    with suppress(RuntimeError, ValueError, KeyError, StopIteration):
        healthy = []
        probe_contract = []
        for pod in pods:
            name = pod["metadata"]["name"]
            body = request(name, "127.0.0.1")
            healthy.append(
                body.get("release") == "dispatch-release-1" and body.get("hostname") == name
            )
            api = next(c for c in pod["spec"]["containers"] if c["name"] == "api")
            startup = api.get("startupProbe", {})
            paths = all(
                api.get(key, {}).get("httpGet", {}).get("path") == path
                for key, path in (
                    ("startupProbe", "/startupz"),
                    ("livenessProbe", "/healthz"),
                    ("readinessProbe", "/readyz"),
                )
            )
            probe_contract.append(
                paths
                and startup.get("periodSeconds", 10) * startup.get("failureThreshold", 3) >= 30
                and pod["spec"].get("terminationGracePeriodSeconds", 30) >= 20
                and request(name, "127.0.0.1", "/startupz").get("started") is True
                and request(name, "127.0.0.1", "/readyz").get("ready") is True
            )
        result["available"] = available(deployment, 2) and len(healthy) == 2 and all(healthy)
        result["probes"] = len(probe_contract) == 2 and all(probe_contract)
    rolling = deployment["spec"].get("strategy", {}).get("rollingUpdate", {})
    result["rollout"] = (
        result["available"]
        and rolling.get("maxUnavailable") in (0, "0%")
        and rolling.get("maxSurge") in (1, "50%")
    )
    sets = [
        rs
        for rs in get("rs")["items"]
        if any(
            owner["uid"] == deployment["metadata"]["uid"]
            for owner in rs["metadata"].get("ownerReferences", [])
        )
    ]
    result["history"] = result["available"] and any(
        any(c["image"] == image + "-missing" for c in rs["spec"]["template"]["spec"]["containers"])
        and rs["spec"].get("replicas", 0) == 0
        for rs in sets
    )
    with suppress(RuntimeError, ValueError, KeyError, IndexError):
        proof = get("pod", "termination-proof")
        status = proof["status"]["containerStatuses"][0]
        log = kubectl("logs", "termination-proof", "--tail=20")
        events = [json.loads(line) for line in log.splitlines() if line.startswith("{")]
        result["termination"] = (
            proof["spec"]["containers"][0]["image"] == image
            and status.get("state", {}).get("terminated", {}).get("exitCode") == 0
            and any(
                event.get("event") == "terminating" and event.get("signal") == 15
                for event in events
            )
        )
    with suppress(RuntimeError, ValueError, KeyError, IndexError):
        candidate, candidate_pods = owned_pods("dispatch-canary")
        client = pods[0]["metadata"]["name"]
        identities = {p["metadata"]["uid"] for p in pods + candidate_pods}
        candidate_ids = {p["metadata"]["uid"] for p in candidate_pods}
        candidate_names = {p["metadata"]["name"] for p in candidate_pods}
        responses = [request(p["metadata"]["name"], "127.0.0.1") for p in candidate_pods]
        body = request(client, "dispatch")
        result["canary"] = (
            result["available"]
            and available(candidate, 1)
            and len(candidate_pods) == 1
            and all(
                response.get("release") == "dispatch-release-2"
                and response.get("hostname") in candidate_names
                for response in responses
            )
            and endpoints("dispatch") == identities
            and len(identities) == 3
            and body.get("hostname") in {p["metadata"]["name"] for p in pods + candidate_pods}
        )
        preview = request(client, "dispatch-preview")
        result["preview"] = (
            available(candidate, 1)
            and endpoints("dispatch-preview") == candidate_ids
            and len(candidate_ids) == 1
            and preview.get("release") == "dispatch-release-2"
            and preview.get("hostname") in candidate_names
        )
    return result
