"""Observe package remediation, credential rejection, and independent restore storage."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from dockyard import host
from dockyard.probes.kubernetes import get, kubectl, owned_pods, sql
from dockyard.probes.security import execute, request
from dockyard.process import run
from dockyard.runtimes.scanner import SCANNER, ready


def findings(report: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (item["PkgName"].lower(), item["VulnerabilityID"])
        for section in report.get("Results", [])
        for item in section.get("Vulnerabilities", [])
    }


def hardening() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(("images", "rotation", "recovery", "workflow"), False)
    details: dict[str, Any] = {}
    result["_details"] = details
    private = Path(os.environ["DOCKYARD_STORAGE"])
    with suppress(RuntimeError, ValueError, KeyError, OSError, IndexError):
        before = json.loads(Path("scan-before.json").read_text())
        after = json.loads(Path("scan-after.json").read_text())
        before_sbom = json.loads(Path("sbom-before.json").read_text())
        after_sbom = json.loads(Path("sbom-after.json").read_text())
        proof = json.loads(Path("scan-evidence-after.json").read_text())
        cache = Path(os.environ["TRIVY_CACHE_DIR"])
        image = os.environ["DOCKYARD_IMAGE"]
        identity = run(
            [
                "docker",
                "image",
                "inspect",
                "--platform=linux/" + host.architecture(),
                "--format",
                "{{.Id}}",
                image,
            ]
        )
        archive = private / "verification-image.tar"
        if archive.is_symlink():
            raise ValueError("Verification archive cannot be a symlink")
        saved = run(
            [
                "docker",
                "image",
                "save",
                "--platform=linux/" + host.architecture(),
                "-o",
                str(archive),
                image,
            ],
            timeout=120,
        )
        if not saved.ok or not ready(cache):
            raise RuntimeError("Pinned scanner inputs are unavailable")
        scanned = run(
            [
                "trivy",
                "image",
                "--disable-telemetry",
                "--skip-version-check",
                "--skip-db-update",
                "--skip-java-db-update",
                "--skip-check-update",
                "--skip-vex-repo-update",
                "--offline-scan",
                "--cache-dir",
                str(cache),
                "--input",
                str(archive),
                "--scanners",
                "vuln",
                "--format",
                "json",
            ],
            timeout=120,
            output_limit=4_000_000,
        )
        actual = json.loads(scanned.stdout)
        archive.unlink(missing_ok=True)
        target = ("pyjwt", "CVE-2022-29217")
        loaded = []
        for deployment in ("dispatch", "worker"):
            _, pods = owned_pods(deployment)
            for pod in pods:
                value = kubectl(
                    "exec",
                    pod["metadata"]["name"],
                    "--",
                    "python",
                    "-c",
                    "import importlib.util,json; "
                    "print(json.dumps(importlib.util.find_spec('jwt') is None))",
                )
                loaded.append(json.loads(value))
        result["images"] = (
            scanned.ok
            and identity.ok
            and proof["lab"] == os.environ["DOCKYARD_LAB"]
            and proof["database"] == SCANNER["database"]
            and identity.stdout.strip() == proof["image_manifest"]
            and actual["Metadata"]["ImageID"]
            == proof["image_configuration"]
            == after["Metadata"]["ImageID"]
            and all(
                hashlib.sha256(Path(name + "-after.json").read_bytes()).hexdigest() == digest
                for name, digest in proof["reports"].items()
            )
            and set(proof["reports"]) == {"scan", "sbom"}
            and target in findings(before)
            and target not in findings(actual)
            and findings(after) == findings(actual)
            and any(
                c["name"].lower() == "pyjwt" and c["version"] == "1.7.1"
                for c in before_sbom["components"]
            )
            and not any(c["name"].lower() == "pyjwt" for c in after_sbom["components"])
            and len(loaded) >= 3
            and all(loaded)
        )
        details["images"] = {
            "removed_cve": target[1],
            "before_present": target in findings(before),
            "after_present": target in findings(actual),
            "remaining_findings": len(findings(actual)),
            "running_processes_without_dependency": sum(loaded),
        }
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        current = base64.b64decode(get("secret", "dispatch-database")["data"]["password"]).decode()
        program = """import json,sys,psycopg
result={}
for name,password in json.load(sys.stdin).items():
    try:
        with psycopg.connect(
            host='db',dbname='dispatch',user='dispatch',
            password=password,connect_timeout=3
        ) as connection:
            connection.execute('SELECT 1')
        result[name]=True
    except psycopg.OperationalError: result[name]=False
print(json.dumps(result))
"""
        measured = run(
            [
                "kubectl",
                "exec",
                "-i",
                "deployment/dispatch",
                "-c",
                "api",
                "--",
                "python",
                "-c",
                program,
            ],
            input_text=json.dumps({"old": os.environ["DOCKYARD_DB_PASSWORD"], "current": current}),
            timeout=20,
        )
        authentication = json.loads(measured.stdout)
        mounted = [
            execute(
                name,
                "import hashlib,json; from pathlib import Path; "
                "print(json.dumps(hashlib.sha256("
                "Path('/var/run/dispatch/password').read_bytes()).hexdigest()))",
            )
            for name in ("dispatch", "worker")
        ]
        result["rotation"] = (
            measured.ok
            and authentication == {"old": False, "current": True}
            and all(value == hashlib.sha256(current.encode()).hexdigest() for value in mounted)
        )
        details["rotation"] = {
            "authentication": authentication,
            "consumers_match_secret": len(set(mounted)) == 1,
        }
    with suppress(RuntimeError, ValueError, KeyError, OSError, InvalidTag, StopIteration):
        backup = json.loads(Path("backup.json").read_text())
        key = private / "backup.key"
        if key.is_symlink() or key.stat().st_mode & 0o077:
            raise ValueError("Backup key permissions are not private")
        cipher = AESGCM(key.read_bytes())
        nonce = base64.b64decode(backup["nonce"])
        ciphertext = base64.b64decode(backup["ciphertext"])
        aad = ("dockyard-backup-v1:" + os.environ["DOCKYARD_LAB"]).encode()
        restored = cipher.decrypt(nonce, ciphertext, aad)
        tamper_rejected = False
        try:
            cipher.decrypt(nonce, ciphertext[:-1] + bytes([ciphertext[-1] ^ 1]), aad)
        except InvalidTag:
            tamper_rejected = True
        source = get("pvc", "data-db-0")
        target_claim = get("pvc", "data-db-recovery-0")
        source_pv = get("pv", source["spec"]["volumeName"])
        target_pv = get("pv", target_claim["spec"]["volumeName"])

        def storage_path(pv: dict[str, Any]) -> str:
            return str(pv["spec"].get("hostPath", pv["spec"].get("local", {})).get("path", ""))

        jobs = request("/jobs")["jobs"]
        marker = backup["marker"]
        found = next(row for row in jobs if row["id"] == marker["id"])
        matches = all(found[k] == marker[k] for k in ("id", "title", "status", "result", "worker"))
        result["recovery"] = (
            backup["schema"] == 1
            and backup["lab"] == os.environ["DOCKYARD_LAB"]
            and hashlib.sha256(restored).hexdigest() == backup["plaintext_sha256"]
            and marker["id"].encode() in restored
            and matches
            and found["status"] == "done"
            and tamper_rejected
            and get("statefulset", "db")["spec"]["replicas"] == 0
            and source["metadata"]["uid"] == backup["source_pvc_uid"]
            and source["spec"]["volumeName"] == backup["source_volume"]
            and source_pv["metadata"]["uid"] != target_pv["metadata"]["uid"]
            and bool(storage_path(target_pv))
            and storage_path(source_pv) != storage_path(target_pv)
            and get("svc", "db")["spec"]["selector"].get("recovery") == "restored"
        )
        details["recovery"] = {
            "marker_recovered": matches,
            "tampered_ciphertext_rejected": tamper_rejected,
            "original_volume": source_pv["metadata"]["name"],
            "restored_volume": target_pv["metadata"]["name"],
            "separate_backing_paths": storage_path(source_pv) != storage_path(target_pv),
        }
    job_id = None
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        workload = (
            "statefulset/db-recovery"
            if get("svc", "db")["spec"]["selector"].get("recovery") == "restored"
            else "statefulset/db"
        )
        try:
            title = "hardened-" + uuid.uuid4().hex
            job_id = request("/jobs", {"title": title}, "POST")["id"]
            if (
                not isinstance(job_id, str)
                or len(job_id) != 32
                or any(c not in "0123456789abcdef" for c in job_id)
            ):
                raise ValueError("Invalid observed job identity")
            deadline = time.monotonic() + 15
            _, workers = owned_pods("worker")
            while time.monotonic() < deadline:
                row = json.loads(
                    sql(f"SELECT row_to_json(j) FROM jobs j WHERE id='{job_id}'", workload=workload)
                )
                if row["status"] == "done":
                    frontend = request("/jobs")["jobs"]
                    visible: dict[str, Any] = next((r for r in frontend if r["id"] == job_id), {})
                    result["workflow"] = (
                        visible.get("status") == "done"
                        and visible.get("result") == row["result"]
                        and row["title"] == title
                        and row["result"]
                        == {
                            "normalized": title.upper(),
                            "sha256": hashlib.sha256(title.encode()).hexdigest(),
                        }
                        and row["worker"] in {p["metadata"]["name"] for p in workers}
                    )
                    break
                time.sleep(0.3)
        finally:
            if (
                isinstance(job_id, str)
                and len(job_id) == 32
                and all(c in "0123456789abcdef" for c in job_id)
            ):
                sql(f"DELETE FROM jobs WHERE id='{job_id}'", workload=workload)
    return result
