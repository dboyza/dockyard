"""Measure actual requests, scrape identities, dashboard data, and alert/SLO rehearsals."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import urllib.parse
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from dockyard.probes.kubernetes import available, get, job_roundtrip, kubectl, owned_pods


def request(url: str) -> dict[str, Any]:
    script = (
        "import json,urllib.request; "
        f"response=urllib.request.urlopen({url!r},timeout=8); "
        'print(json.dumps({"body":json.load(response),"request_id":response.headers.get("X-Request-ID")}))'
    )
    return dict(
        json.loads(
            kubectl(
                "exec", "deployment/dispatch", "-c", "api", "--", "python", "-c", script, timeout=20
            )
        )
    )


# Four of the lab's five-second scrape intervals.
SCRAPE_WAIT_SECONDS = 20


def serve(pod: str) -> None:
    """Send one GET /jobs to this API Pod, from inside it, so it counts a request."""
    script = (
        "import urllib.request; "
        "urllib.request.urlopen('http://127.0.0.1:8080/jobs', timeout=8).read()"
    )
    kubectl("exec", pod, "-c", "api", "--", "python", "-c", script, timeout=20)


def prometheus(path: str) -> dict[str, Any]:
    return dict(request("http://prometheus:9090" + path)["body"])


def query(expression: str) -> list[dict[str, Any]]:
    return list(
        prometheus("/api/v1/query?" + urllib.parse.urlencode({"query": expression}))["data"][
            "result"
        ]
    )


def valid_window(record: dict[str, Any], lab_id: str) -> bool:
    samples = record["samples"]
    good = sum(s["valid"] and s["status"] == 200 and s["seconds"] <= 0.25 for s in samples)
    return bool(
        record["lab"] == lab_id
        and record["objective"] == 0.95
        and record["latency_seconds"] == 0.25
        and len(samples) == record["total"] == 20
        and record["good"] == good
        and math.isclose(record["ratio"], good / len(samples))
        and all(isinstance(s["seconds"], (int, float)) and 0 <= s["seconds"] <= 5 for s in samples)
        and all(
            isinstance(s.get("request_id"), str) and len(s["request_id"]) == 32 for s in samples
        )
    )


def visibility() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(
        ("signals", "scraping", "dashboard", "alert", "slo"), False
    )
    details: dict[str, Any] = {}
    result["_details"] = details
    deployment, pods = owned_pods("dispatch")
    if not available(deployment, 2) or len(pods) != 2:
        return result
    with suppress(RuntimeError, ValueError, KeyError):
        response = request("http://dispatch:8080/jobs")
        identity = response["request_id"]
        matched = []
        for pod in pods:
            lines = kubectl("logs", pod["metadata"]["name"], "-c", "api", "--tail=100").splitlines()
            for line in lines:
                with suppress(ValueError):
                    event = json.loads(line)
                    if event.get("event") == "http_request" and event.get("request_id") == identity:
                        matched.append(event)
        result["signals"] = bool(
            isinstance(response["body"].get("jobs"), list)
            and len(matched) == 1
            and matched[0]["status"] == 200
            and matched[0]["route"] == "/jobs"
            and matched[0]["duration_seconds"] > 0
        )
        details["signals"] = {"request_id": identity, "matching_events": matched}
    with suppress(RuntimeError, ValueError, KeyError):
        # Each Pod only reports a request counter once it has served a request, and
        # Prometheus only sees it at its next scrape: serve every Pod, then allow a
        # few scrape intervals rather than depending on where earlier traffic landed.
        for pod in pods:
            serve(pod["metadata"]["name"])
        settle_until = time.monotonic() + SCRAPE_WAIT_SECONDS
        while True:
            targets = prometheus("/api/v1/targets")["data"]["activeTargets"]
            actual = {pod["metadata"]["uid"] for pod in pods}
            healthy = {
                t["discoveredLabels"].get("__meta_kubernetes_pod_uid")
                for t in targets
                if t["health"] == "up" and t["labels"].get("job") == "dispatch"
            }
            traffic = query(
                'dispatch_http_requests_total{job="dispatch",route="/jobs",status="200"}'
            )
            measured = {v["metric"].get("pod") for v in traffic if float(v["value"][1]) > 0}
            result["scraping"] = (
                actual <= healthy and {p["metadata"]["name"] for p in pods} <= measured
            )
            if result["scraping"] or time.monotonic() >= settle_until:
                break
            time.sleep(2)
        details["scraping"] = {
            "targets": [
                {
                    "pod": t["labels"].get("pod"),
                    "health": t["health"],
                    "error": t.get("lastError"),
                    "last_scrape": t.get("lastScrape"),
                }
                for t in targets
            ],
            "measured_pods": sorted(measured),
        }
    with suppress(RuntimeError, ValueError, KeyError, IndexError):
        dashboard = request("http://metrics-dashboard:8081/data")["body"]
        panels = {p["id"]: p for p in dashboard["panels"]}
        values = {
            key: float(panels[key]["data"][0]["values"][-1][1])
            for key in ("rate", "latency", "p95")
        }
        result["dashboard"] = (
            result["scraping"]
            and all(math.isfinite(v) for v in values.values())
            and values["rate"] > 0
            and 0 <= values["latency"] <= 1
            and 0 < values["p95"] <= 5
        )
        details["dashboard"] = values
    with suppress(OSError, RuntimeError, ValueError, KeyError, IndexError, StopIteration):
        record = json.loads(Path("alert-evidence.json").read_text())
        rules = prometheus("/api/v1/rules")["data"]["groups"]
        rule = next(
            r for group in rules for r in group["rules"] if r["name"] == "DispatchLatencyBudgetBurn"
        )
        source = yaml.safe_load(Path("rules.yaml").read_text())["groups"][0]["rules"][0]
        live = yaml.safe_load(get("cm", "prometheus-config")["data"]["rules.yaml"])["groups"][0][
            "rules"
        ][0]
        result["alert"] = (
            result["scraping"]
            and record["lab"] == os.environ["DOCKYARD_LAB"]
            and record["failure"]["firing"] is True
            and record["failure"]["good_ratio"] < 0.9
            and record["recovery"]["firing"] is False
            and record["recovery"]["good_ratio"] >= 0.95
            and datetime.fromisoformat(record["started_at"])
            < datetime.fromisoformat(record["failure"]["at"])
            < datetime.fromisoformat(record["recovery"]["at"])
            and record["rules_sha256"]
            == hashlib.sha256(Path("rules.yaml").read_bytes()).hexdigest()
            and record["dashboard_sha256"]
            == hashlib.sha256(Path("dashboard.json").read_bytes()).hexdigest()
            and source == live
            and rule["duration"] == 15
            and rule["state"] == "inactive"
            and rule["labels"].get("severity") == "warning"
            and bool(rule.get("annotations", {}).get("summary"))
            and bool(rule.get("annotations", {}).get("runbook"))
            and get("cm", "dispatch-settings")["data"]["delay_ms"] == "20"
        )
        details["alert"] = {
            "rehearsal": record,
            "current_state": rule["state"],
            "expression": rule["query"],
        }
    with suppress(OSError, RuntimeError, ValueError, KeyError):
        before = json.loads(Path("slo-before.json").read_text())
        after = json.loads(Path("slo-after.json").read_text())
        policy = json.loads(Path("slo.json").read_text())
        settings = get("cm", "dispatch-settings")["data"]
        # Measure current service behavior as well as inspecting the authored rehearsal record.
        script = (
            "import json,time,urllib.request; start=time.perf_counter(); "
            'response=urllib.request.urlopen("http://dispatch:8080/jobs",timeout=3); '
            'body=json.load(response); print(json.dumps({"seconds":time.perf_counter()-start,'
            '"valid":isinstance(body.get("jobs"),list)}))'
        )
        current = json.loads(
            kubectl("exec", "deployment/dispatch", "-c", "api", "--", "python", "-c", script)
        )
        result["slo"] = (
            valid_window(before, os.environ["DOCKYARD_LAB"])
            and valid_window(after, os.environ["DOCKYARD_LAB"])
            and before["ratio"] < 0.95 <= after["ratio"]
            and policy["objective"] == 0.95
            and policy["latency_seconds"] == 0.25
            and settings["delay_ms"] == "20"
            and datetime.fromisoformat(before["finished_at"])
            < datetime.fromisoformat(after["started_at"])
            and current["valid"]
            and current["seconds"] <= 0.25
        )
        details["slo"] = {
            "before": {k: v for k, v in before.items() if k != "samples"},
            "after": {k: v for k, v in after.items() if k != "samples"},
            "current_request": current,
        }
    return result


# busybox ps prints "PID USER TIME COMMAND"; with --target the API process is PID 1.
TARGET_PROCESS = re.compile(r"^\s*1\s+\S+\s+\S+\s+python app\.py\s*$", re.MULTILINE)


def debugging() -> dict[str, Any]:
    """Observe an ephemeral container on a live API Pod, running workers, and no stray copies."""
    result: dict[str, Any] = dict.fromkeys(("processes", "worker", "cleanup"), False)
    details: dict[str, Any] = {}
    result["_details"] = details
    with suppress(RuntimeError, ValueError, KeyError):
        _, pods = owned_pods("dispatch")
        targeted = [
            pod["metadata"]["name"]
            for pod in pods
            if any(
                container.get("targetContainerName") == "api"
                for container in pod["spec"].get("ephemeralContainers", [])
            )
        ]
        details["targeted_pods"] = targeted
        evidence = Path("api-processes.txt")
        details["evidence"] = evidence.exists()
        result["processes"] = bool(targeted) and bool(
            evidence.exists() and TARGET_PROCESS.search(evidence.read_text(errors="replace"))
        )
    with suppress(RuntimeError, ValueError, KeyError):
        deployment, pods = owned_pods("worker")
        details["worker_restarts"] = {
            pod["metadata"]["name"]: [
                status.get("restartCount", 0)
                for status in pod["status"].get("containerStatuses", [])
            ]
            for pod in pods
        }
        result["worker"] = (
            available(deployment, 2)
            and len(pods) == 2
            and all(
                status.get("ready") and "running" in status.get("state", {})
                for pod in pods
                for status in pod["status"].get("containerStatuses", [])
            )
        )
    with suppress(RuntimeError, ValueError, KeyError):
        unowned = [
            pod["metadata"]["name"]
            for pod in get("pods")["items"]
            if not pod["metadata"].get("ownerReferences")
            and not pod["metadata"].get("deletionTimestamp")
        ]
        details["unowned_pods"] = unowned
        result["cleanup"] = not unowned
    try:
        result["processing"] = job_roundtrip()
    except (RuntimeError, ValueError, KeyError):
        result["processing"] = False
    return result
