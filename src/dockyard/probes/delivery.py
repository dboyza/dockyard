"""Observe tested registry content, Git revisions, and real Flux-applied workload state."""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import yaml

from dockyard.catalog import CONTENT
from dockyard.probes.kubernetes import available, get, job_roundtrip, kubectl, owned_pods
from dockyard.process import run


def git(*args: str) -> str:
    result = run(["git", "-C", "delivery", *args], timeout=20)
    if not result.ok:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def ready(item: dict[str, Any]) -> bool:
    return any(
        condition["type"] == "Ready"
        and condition["status"] == "True"
        and condition.get("observedGeneration") == item["metadata"]["generation"]
        for condition in item.get("status", {}).get("conditions", [])
    )


def delivery() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(
        ("pipeline", "reconciliation", "identity", "drift", "promotion", "rollback", "workflow"),
        False,
    )
    details: dict[str, Any] = {}
    result["_details"] = details
    release: dict[str, Any] = {}
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        release = json.loads(Path("release.json").read_text())
        registry = os.environ["DOCKYARD_REGISTRY"]
        version = Path("VERSION").read_text().strip()
        request = Request(
            f"http://{registry}/v2/dispatch/manifests/{version}",
            headers={
                "Accept": "application/vnd.oci.image.index.v1+json, "
                "application/vnd.docker.distribution.manifest.v2+json"
            },
        )
        with urlopen(request, timeout=5) as response:
            manifest = response.read(1_000_000)
            digest = response.headers["Docker-Content-Digest"]
        expected = f"{registry}/dispatch@{digest}"
        # The packaged contract independently exercises the published image's HTTP behavior.
        test = (CONTENT / "checkpoints/dispatch-delivery-v1/test_release.py").read_text()
        test = test.replace('Path("VERSION").read_text().strip()', repr(version))
        tested = run(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--network=none",
                "--label",
                "io.dockyard.lab=" + os.environ["DOCKYARD_LAB"],
                expected,
                "python",
                "-",
            ],
            input_text=test,
            timeout=45,
        )
        source_files = release.get("source_sha256", {})
        result["pipeline"] = (
            release["lab"] == os.environ["DOCKYARD_LAB"]
            and release["version"] == version
            and release["tested"] is True
            and release["image"] == expected
            and release["digest"] == digest == "sha256:" + hashlib.sha256(manifest).hexdigest()
            and tested.ok
            and release["test_sha256"]
            == hashlib.sha256(Path("test_release.py").read_bytes()).hexdigest()
            and set(source_files)
            == {
                ".dockerignore",
                "Dockerfile",
                "app.py",
                "database.py",
                "worker.py",
                "maintenance.py",
                "dashboard.html",
                "VERSION",
                "requirements.txt",
            }
            and all(
                hashlib.sha256(Path(p).read_bytes()).hexdigest() == d
                for p, d in source_files.items()
            )
        )
        details["pipeline"] = {
            "version": version,
            "registry_digest": digest,
            "recorded_test_gate": release["tested"],
            "independent_http_tests": tested.ok,
        }
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        head = git("rev-parse", "HEAD")
        remote = git("ls-remote", "origin", "refs/heads/main").split()[0]
        source = get("gitrepository.source.toolkit.fluxcd.io", "dispatch", "flux-system")
        conditions = []
        live_images = []
        for environment, name, count in (
            ("development", "dispatch", 2),
            ("staging", "dispatch-staging", 1),
        ):
            kustomization = get(
                "kustomization.kustomize.toolkit.fluxcd.io", environment, "flux-system"
            )
            desired = yaml.safe_load(
                git("show", f"HEAD:environments/{environment}/deployment.yaml")
            )
            deployment, pods = owned_pods(name)
            expected = desired["spec"]["template"]["spec"]["containers"][0]["image"]
            live = deployment["spec"]["template"]["spec"]["containers"][0]["image"]
            responses = [
                json.loads(
                    kubectl(
                        "exec",
                        p["metadata"]["name"],
                        "-c",
                        "api",
                        "--",
                        "python",
                        "-c",
                        "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/healthz',timeout=3).read().decode())",
                    )
                )
                for p in pods
            ]
            conditions.append(
                ready(kustomization)
                and not kustomization["spec"].get("suspend", False)
                and kustomization["spec"]["serviceAccountName"] == "dispatch-deployer"
                and kustomization["status"]["lastAppliedRevision"].endswith(":" + head)
                and available(deployment, count)
                and len(pods) == count
                and "@sha256:" in expected
                and expected == live
                and all(r["release"] == release.get("version") for r in responses)
            )
            live_images.append(live)
        result["reconciliation"] = (
            head == remote
            and git("remote", "get-url", "origin") == os.environ["DOCKYARD_GIT_URL"]
            and not git("status", "--porcelain")
            and source["spec"]["url"] == os.environ["DOCKYARD_GIT_CLUSTER_URL"]
            and ready(source)
            and source["status"]["artifact"]["revision"].endswith(":" + head)
            and all(conditions)
        )
        details["reconciliation"] = {
            "local_commit": head,
            "remote_commit": remote,
            "live_images": live_images,
            "environments_ready": conditions,
        }
        identity = "system:serviceaccount:flux-system:dispatch-deployer"
        result["identity"] = (
            kubectl("auth", "can-i", "patch", "deployments", "--as", identity) == "yes"
            and run(["kubectl", "auth", "can-i", "get", "secrets", "--as", identity]).stdout.strip()
            == "no"
            and run(
                [
                    "kubectl",
                    "auth",
                    "can-i",
                    "patch",
                    "deployments",
                    "-n",
                    "kube-system",
                    "--as",
                    identity,
                ]
            ).stdout.strip()
            == "no"
        )
        record = json.loads(Path("delivery-evidence.json").read_text())
        current = get("deployment", "dispatch")
        generations = record["generations"]
        result["drift"] = (
            result["reconciliation"]
            and record["lab"] == os.environ["DOCKYARD_LAB"]
            and record["deployment_uid"] == current["metadata"]["uid"]
            and record["replicas"] == [2, 0, 2]
            and len(generations) == 3
            and generations[0]
            < generations[1]
            < generations[2]
            <= current["metadata"]["generation"]
        )

        def image_at(commit: str, environment: str) -> str:
            document = yaml.safe_load(
                git("show", f"{commit}:environments/{environment}/deployment.yaml")
            )
            return str(document["spec"]["template"]["spec"]["containers"][0]["image"])

        dev, promotion, fault, recovery = (
            record[k + "_commit"] for k in ("development", "promotion", "fault", "recovery")
        )
        result["promotion"] = (
            result["pipeline"]
            and result["reconciliation"]
            and image_at(dev, "development") == image_at(promotion, "staging") == release["image"]
            and image_at(dev, "staging") != image_at(promotion, "staging")
            and git("rev-parse", promotion + "^") == dev
            and record["digest"] == release["digest"]
            and release["version"] == "dispatch-3"
        )
        result["rollback"] = (
            result["promotion"]
            and recovery == head
            and git("rev-parse", recovery + "^") == fault
            and git("rev-parse", fault + "^") == promotion
            and git("rev-parse", recovery + "^{tree}") == git("rev-parse", promotion + "^{tree}")
            and image_at(fault, "staging") == record["failure"]["image"]
            and record["failure"]["reason"] in ("ErrImagePull", "ImagePullBackOff")
            and image_at(fault, "staging") != release["image"]
        )
        for criterion in ("drift", "promotion", "rollback"):
            details[criterion] = record
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        result["workflow"] = job_roundtrip(database_workload="statefulset/db")
    return result
