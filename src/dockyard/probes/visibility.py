"""Measure actual requests, scrape identities, dashboard data, and alert/SLO rehearsals."""

from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.parse
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from dockyard.probes.kubernetes import available, get, kubectl, owned_pods


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
        targets = prometheus("/api/v1/targets")["data"]["activeTargets"]
        actual = {pod["metadata"]["uid"] for pod in pods}
        healthy = {
            t["discoveredLabels"].get("__meta_kubernetes_pod_uid")
            for t in targets
            if t["health"] == "up" and t["labels"].get("job") == "dispatch"
        }
        traffic = query('dispatch_http_requests_total{job="dispatch",route="/jobs",status="200"}')
        measured = {v["metric"].get("pod") for v in traffic if float(v["value"][1]) > 0}
        result["scraping"] = actual <= healthy and {p["metadata"]["name"] for p in pods} <= measured
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
