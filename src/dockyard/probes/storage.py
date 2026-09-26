"""Read database and storage identities without replacing learner Pods during checks."""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import suppress
from typing import Any

from dockyard.probes.kubernetes import api_request, get, kubectl


def database_pod(label: str) -> dict[str, Any]:
    pods = [
        pod
        for pod in get("pods")["items"]
        if pod["metadata"].get("labels", {}).get("app") == label
        and not pod["metadata"].get("deletionTimestamp")
        and any(
            c["type"] == "Ready" and c["status"] == "True"
            for c in pod.get("status", {}).get("conditions", [])
        )
    ]
    if len(pods) != 1:
        raise ValueError("Exactly one ready database Pod is required.")
    return dict(pods[0])


def storage_identity(pod: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    container = next(c for c in pod["spec"]["containers"] if c["name"] == "database")
    mount = next(
        m for m in container["volumeMounts"] if m["mountPath"] == "/var/lib/postgresql/data"
    )
    volume = next(v for v in pod["spec"]["volumes"] if v["name"] == mount["name"])
    claim = get("pvc", volume["persistentVolumeClaim"]["claimName"])
    pv = get("pv", claim["spec"]["volumeName"])
    if claim.get("status", {}).get("phase") != "Bound" or (
        pv["spec"]["claimRef"]["uid"] != claim["metadata"]["uid"]
    ):
        raise ValueError("The database volume is not bound to its claim.")
    return claim, pv


def query(pod: dict[str, Any], statement: str) -> str:
    return kubectl(
        "exec",
        pod["metadata"]["name"],
        "--",
        "psql",
        "-U",
        "dispatch",
        "-d",
        "dispatch",
        "-At",
        "-c",
        statement,
    )


def backing_volume(volume: dict[str, Any]) -> str:
    spec = volume["spec"]
    for kind in ("hostPath", "local"):
        if kind in spec:
            return f"{kind}:{spec[kind]['path']}"
    if "csi" in spec:
        return f"csi:{spec['csi']['driver']}:{spec['csi']['volumeHandle']}"
    return ""


def storage() -> dict[str, bool]:
    result = dict.fromkeys(("claim", "persistence", "identity", "restore"), False)
    try:
        pod = database_pod("db")
        claim, pv = storage_identity(pod)
        result["claim"] = True
    except (RuntimeError, ValueError, KeyError, StopIteration):
        return result
    token = hashlib.sha256(os.environ["DOCKYARD_LAB"].encode()).hexdigest()
    with suppress(RuntimeError, ValueError, KeyError):
        marker = json.loads(query(pod, "SELECT row_to_json(p) FROM durability_proof p WHERE id=1"))
        result["persistence"] = (
            marker["token"] == token
            and marker["original_pod"] != pod["metadata"]["uid"]
            and len(marker["original_pod"]) == 36
            and api_request("/readyz").get("ready") is True
        )
    with suppress(RuntimeError, ValueError, KeyError, StopIteration):
        workload = get("statefulset", "db")
        spec = workload["spec"]
        service = get("svc", spec["serviceName"])
        result["identity"] = (
            pod["metadata"]["name"] == "db-0"
            and any(
                owner["uid"] == workload["metadata"]["uid"]
                for owner in pod["metadata"].get("ownerReferences", [])
            )
            and spec.get("replicas", 1) == 1
            and spec.get("persistentVolumeClaimRetentionPolicy", {}).get("whenDeleted", "Retain")
            == "Retain"
            and spec.get("persistentVolumeClaimRetentionPolicy", {}).get("whenScaled", "Retain")
            == "Retain"
            and service["spec"].get("clusterIP") == "None"
            and service["spec"].get("selector", {}).get("app") == "db"
            and any(
                claim["metadata"]["name"] == f"{template['metadata']['name']}-db-0"
                for template in spec.get("volumeClaimTemplates", [])
            )
        )
    with suppress(RuntimeError, ValueError, KeyError, StopIteration):
        restored = database_pod("db-restore")
        target_claim, target_pv = storage_identity(restored)
        statement = "SELECT json_agg(r ORDER BY id) FROM recovery_records r"
        source_rows = json.loads(query(pod, statement))
        target_rows = json.loads(query(restored, statement))
        expected = [
            {"id": 1, "title": "Preserve this exact record"},
            {"id": 2, "title": "Restore into a separate volume"},
        ]
        restored_marker = query(restored, "SELECT token FROM durability_proof WHERE id=1")
        result["restore"] = (
            source_rows == target_rows == expected
            and restored_marker == token
            and claim["metadata"]["uid"] != target_claim["metadata"]["uid"]
            and pv["metadata"]["uid"] != target_pv["metadata"]["uid"]
            and bool(backing_volume(pv))
            and backing_volume(pv) != backing_volume(target_pv)
        )
    return result
