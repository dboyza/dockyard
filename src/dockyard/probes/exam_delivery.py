"""Observed delivery outcomes for the second original CKAD practice exam."""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any

import yaml

from dockyard.fixtures.incident import baseline_path
from dockyard.probes.capacity import quantity
from dockyard.probes.exam import ERRORS
from dockyard.probes.kubernetes import available, get, kubectl, owned_pods
from dockyard.probes.registry_incident import registry
from dockyard.probes.releases import endpoints, request


def delivery() -> dict[str, Any]:
    result = registry()
    result.update(
        dict.fromkeys(
            (
                "digest",
                "credential",
                "resources",
                "overlay",
                "preview",
                "listener",
                "archive",
                "routing",
            ),
            False,
        )
    )
    baseline = json.loads(baseline_path().read_text())
    with suppress(*ERRORS):
        original = json.loads(
            (
                Path(os.environ["DOCKYARD_DATA"])
                / "labs"
                / os.environ["DOCKYARD_LAB"]
                / "data/registry-release.json"
            ).read_text()
        )
        _, pods = owned_pods("dispatch")
        result["digest"] = (
            result["contract"]
            and len(pods) == 2
            and all(
                next(c for c in p["spec"]["containers"] if c["name"] == "api")["image"]
                == original["registry"] + "/dispatch@" + original["digest"]
                for p in pods
            )
        )
        result["credential"] = len(pods) == 2 and all(
            p["spec"].get("automountServiceAccountToken") is False
            and request(p["metadata"]["name"], "127.0.0.1", "/readyz").get("ready") is True
            and kubectl(
                "exec",
                p["metadata"]["name"],
                "-c",
                "api",
                "--",
                "python",
                "-c",
                "import pathlib; "
                "print(pathlib.Path('/var/run/secrets/kubernetes.io/serviceaccount/token').exists())",
            )
            == "False"
            for p in pods
        )
    with suppress(*ERRORS):
        d, workers = owned_pods("worker")
        contracts = []
        for pod in workers:
            c = next(c for c in pod["spec"]["containers"] if c["name"] == "worker")
            r = c.get("resources", {})
            requests, limits = r.get("requests", {}), r.get("limits", {})
            memory = int(
                kubectl("exec", pod["metadata"]["name"], "--", "cat", "/sys/fs/cgroup/memory.max")
            )
            contracts.append(
                0 < quantity(requests.get("cpu", "0")) <= quantity(limits.get("cpu", "0")) <= 0.5
                and 32 * 1024**2
                <= quantity(requests.get("memory", "0"))
                <= quantity(limits.get("memory", "0"))
                <= 256 * 1024**2
                and memory == quantity(limits.get("memory", "0"))
            )
        result["resources"] = available(d, 2) and len(contracts) == 2 and all(contracts)
    with suppress(*ERRORS):
        built = list(yaml.safe_load_all(kubectl("kustomize", "release/overlays/production")))
        metadata = next(
            d
            for d in built
            if d["kind"] == "ConfigMap" and d["metadata"]["name"].startswith("release-metadata")
        )
        workload = next(
            d
            for d in built
            if d["kind"] == "Deployment" and d["metadata"]["name"] == "metadata-reader"
        )
        live, pods = owned_pods("metadata-reader")
        live_cm = get("configmap", metadata["metadata"]["name"])
        actual = json.loads(
            kubectl(
                "exec",
                "deployment/metadata-reader",
                "--",
                "python",
                "-c",
                "import json,urllib.request; "
                "print(json.dumps({k:urllib.request.urlopen('http://127.0.0.1:8080/'+k)"
                ".read().decode().strip() "
                "for k in ('environment','release')}))",
            )
        )
        result["overlay"] = (
            available(live, 1)
            and actual == {"environment": "production", "release": "dispatch-approved-b"}
            and metadata["data"] == live_cm["data"]
            and metadata["data"] == actual
            and any(
                v.get("configMap", {}).get("name") == metadata["metadata"]["name"]
                for v in workload["spec"]["template"]["spec"]["volumes"]
            )
            and all(
                any(
                    v.get("configMap", {}).get("name") == metadata["metadata"]["name"]
                    for v in p["spec"]["volumes"]
                )
                for p in pods
            )
        )
    with suppress(*ERRORS):
        d, pods = owned_pods("preview-api")
        strategy = d["spec"]["strategy"].get("rollingUpdate", {})
        result["preview"] = (
            available(d, 2)
            and len(pods) == 2
            and strategy.get("maxUnavailable") in (0, "0%")
            and strategy.get("maxSurge") in (1, "50%")
            and all(
                request(p["metadata"]["name"], "127.0.0.1").get("release") == "dispatch-preview-b"
                for p in pods
            )
        )
        _, stable = owned_pods("dispatch")
        source = stable[0]["metadata"]["name"]
        result["routing"] = (
            endpoints("preview") == {p["metadata"]["uid"] for p in pods}
            and endpoints("dispatch") == {p["metadata"]["uid"] for p in stable}
            and request(source, "preview").get("release") == "dispatch-preview-b"
            and request(source, "dispatch").get("release") == baseline["stable_release"]
        )
    with suppress(*ERRORS):
        d, pods = owned_pods("report-listener")
        ports = get("service", "reports")["spec"]["ports"]
        body = kubectl(
            "exec",
            "deployment/metadata-reader",
            "--",
            "python",
            "-c",
            "import urllib.request; print(urllib.request.urlopen('http://reports:8080/',timeout=3).status)",
        )
        result["listener"] = (
            available(d, 1)
            and len(pods) == 1
            and any(p["port"] == 8080 and p["targetPort"] == 8090 for p in ports)
            and body == "200"
            and any(
                e["name"] == "PORT" and e.get("value") == "8090"
                for e in pods[0]["spec"]["containers"][0].get("env", [])
            )
        )
    with suppress(*ERRORS):
        claim = get("pvc", "report-cache")
        d, pods = owned_pods("report-cache")
        digest = kubectl(
            "exec",
            "deployment/report-cache",
            "--",
            "python",
            "-c",
            "from pathlib import Path; import hashlib; "
            "print(hashlib.sha256(Path('/archive/report.json').read_bytes()).hexdigest())",
        )
        mounted = all(
            any(
                v.get("persistentVolumeClaim", {}).get("claimName") == "report-cache"
                and any(
                    m["name"] == v["name"] and m["mountPath"] == "/archive"
                    for c in p["spec"]["containers"]
                    for m in c.get("volumeMounts", [])
                )
                for v in p["spec"]["volumes"]
            )
            for p in pods
        )
        result["archive"] = (
            available(d, 1)
            and claim["metadata"]["uid"] == baseline["report-cache"]
            and mounted
            and digest == baseline["report_hash"]
            and hashlib.sha256(Path("report-backup.json").read_bytes()).hexdigest()
            == baseline["report_hash"]
        )
    return result


if __name__ == "__main__":
    print(json.dumps(delivery()))
