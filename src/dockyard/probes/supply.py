"""Observe supply chain outcomes: manifest analysis, signed images, and admitted registries."""

from __future__ import annotations

import json
import os
import re
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

from dockyard.probes.kubernetes import available, job_roundtrip, kubectl, owned_pods
from dockyard.process import run

# kubesec points for the Deployment; the reference earns 14, an unhardened one goes negative.
MINIMUM_SCORE = 10


def rendered(name: str) -> str:
    """A workspace manifest as it is deployed, with this lab's values filled in."""
    return re.sub(
        r"\$\{(DOCKYARD_[A-Z_]+)\}",
        lambda match: os.environ[match.group(1)],
        Path(name).read_text(),
    )


def lint(manifest: str) -> dict[str, Any]:
    result = run(["kube-linter", "lint", "-"], input_text=manifest, timeout=60)
    checks = sorted(set(re.findall(r"\(check: ([a-z0-9-]+)", result.stdout + result.stderr)))
    return {"clean": result.ok, "failed_checks": checks}


def score(manifest: str, kind: str = "Deployment") -> dict[str, Any]:
    result = run(["kubesec", "scan", "-"], input_text=manifest, timeout=60)
    reports = json.loads(result.stdout)
    report = next(item for item in reports if item["object"].startswith(kind + "/"))
    critical = [item["id"] for item in report["scoring"].get("critical", [])]
    return {"score": report["score"], "critical": critical}


def growing(namespace: str, target: str, folder: str) -> bool:
    count = f"ls {folder} | wc -l"

    def files() -> int:
        return int(kubectl("exec", "-n", namespace, target, "--", "sh", "-c", count).strip())

    before = files()
    time.sleep(6)
    return files() > before


def analysis() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(("lint", "score", "deployed"), False)
    details: dict[str, Any] = {}
    result["_details"] = details
    with suppress(RuntimeError, ValueError, KeyError, OSError, StopIteration):
        manifest = rendered("resizer.yaml")
        details["lint"] = lint(manifest)
        result["lint"] = details["lint"]["clean"]
        details["score"] = score(manifest)
        result["score"] = (
            details["score"]["score"] >= MINIMUM_SCORE and not details["score"]["critical"]
        )
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        deployment, pods = owned_pods("resizer", "media")
        spec = deployment["spec"]["template"]["spec"]
        container = spec["containers"][0]
        context = container.get("securityContext", {})
        pod_context = spec.get("securityContext", {})
        # The deployed workload must match the reviewed file, not just the file on disk.
        live = {
            "privileged": bool(context.get("privileged")),
            "host_paths": [v["name"] for v in spec.get("volumes", []) if "hostPath" in v],
            "non_root": bool(context.get("runAsNonRoot", pod_context.get("runAsNonRoot"))),
            "read_only_root": context.get("readOnlyRootFilesystem") is True,
        }
        details["deployed"] = live
        result["deployed"] = (
            available(deployment, 1)
            and len(pods) == 1
            and not live["privileged"]
            and not live["host_paths"]
            and live["non_root"]
            and live["read_only_root"]
            and growing("media", "deployment/resizer", "/work/thumbnails")
        )
    try:
        result["processing"] = job_roundtrip()
    except (RuntimeError, ValueError, KeyError):
        result["processing"] = False
    return result


def release() -> dict[str, str]:
    """The release the lab published, recorded outside the workspace."""
    from dockyard.fixtures.supply import current

    record = json.loads((current().root / "data/release.json").read_text())
    return {"registry": record["registry"], "digest": record["digest"]}


def admitted(namespace: str, image: str) -> bool:
    """Whether the API server would admit a Deployment with this image, without creating it."""
    result = run(
        [
            "kubectl",
            "create",
            "deployment",
            "admission-probe",
            "-n",
            namespace,
            "--image",
            image,
            "--dry-run=server",
        ],
        timeout=30,
    )
    return result.ok


def signing() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(("signed", "admission", "deployed"), False)
    details: dict[str, Any] = {}
    result["_details"] = details
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        published = release()
        reference = f"{published['registry']}/dispatch@{published['digest']}"
        verified = run(
            ["cosign", "verify", "--key", "cosign.pub", "--insecure-ignore-tlog=true", reference],
            timeout=60,
        )
        details["signed"] = {"verified": verified.ok, "public_key": Path("cosign.pub").exists()}
        result["signed"] = verified.ok
        cases = {
            "unapproved_registry": (os.environ["DOCKYARD_BUSYBOX_LOCAL_IMAGE"], False),
            "release_registry_by_tag": (f"{published['registry']}/dispatch:1.0", False),
            "release_registry_by_digest": (reference, True),
        }
        outcomes = {case: admitted("production", image) for case, (image, _) in cases.items()}
        details["admission"] = outcomes
        result["admission"] = all(outcomes[case] == wanted for case, (_, wanted) in cases.items())
        deployment, pods = owned_pods("dispatch", "production")
        images = [c["image"] for c in deployment["spec"]["template"]["spec"]["containers"]]
        details["deployed"] = {"images": images}
        result["deployed"] = images == [reference] and available(deployment, 1) and len(pods) == 1
    try:
        result["processing"] = job_roundtrip()
    except (RuntimeError, ValueError, KeyError):
        result["processing"] = False
    return result


def image_minimal(reference: str) -> dict[str, Any]:
    """Pull an image and inspect a stopped, lab-labelled container made from it."""
    from dockyard.probes.docker import filesystem_findings, nonroot

    pulled = run(["docker", "pull", "-q", reference], timeout=180)
    if not pulled.ok:
        raise RuntimeError("The deployed image could not be pulled from the release registry.")
    created = run(
        ["docker", "create", "--label", "io.dockyard.lab=" + os.environ["DOCKYARD_LAB"], reference],
        timeout=60,
    )
    if not created.ok:
        raise RuntimeError("A container could not be created from the deployed image.")
    container = created.stdout.strip()
    try:
        configured = json.loads(
            run(["docker", "inspect", "--format", "{{json .Config.User}}", container]).stdout
        )
        found = filesystem_findings(container)
    finally:
        run(["docker", "rm", "-f", container], timeout=30)
    return {
        "user": configured,
        **found,
        "ok": nonroot(str(configured or "")) and not any(found.values()),
    }


def release_mission() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(
        ("minimal", "signed", "analysis", "admission", "deployed"), False
    )
    details: dict[str, Any] = {}
    result["_details"] = details
    with suppress(RuntimeError, ValueError, KeyError, OSError, StopIteration):
        registry = release()["registry"]
        deployment, pods = owned_pods("dispatch", "production")
        images = [c["image"] for c in deployment["spec"]["template"]["spec"]["containers"]]
        reference = images[0]
        by_digest = len(images) == 1 and reference.startswith(registry + "/dispatch@sha256:")
        details["deployed"] = {"images": images}
        result["deployed"] = by_digest and available(deployment, 1) and len(pods) == 1
        if by_digest:
            details["minimal"] = image_minimal(reference)
            result["minimal"] = details["minimal"]["ok"]
            verified = run(
                [
                    "cosign",
                    "verify",
                    "--key",
                    "cosign.pub",
                    "--insecure-ignore-tlog=true",
                    reference,
                ],
                timeout=60,
            )
            details["signed"] = {"verified": verified.ok}
            result["signed"] = verified.ok
            cases = {
                "unapproved_registry": (os.environ["DOCKYARD_BUSYBOX_LOCAL_IMAGE"], False),
                "release_registry_by_tag": (f"{registry}/dispatch:1.0", False),
                "release_by_digest": (reference, True),
            }
            outcomes = {case: admitted("production", image) for case, (image, _) in cases.items()}
            details["admission"] = outcomes
            result["admission"] = all(
                outcomes[case] == wanted for case, (_, wanted) in cases.items()
            )
    with suppress(RuntimeError, ValueError, KeyError, OSError, StopIteration):
        manifest = rendered("production.yaml")
        linted, scored = lint(manifest), score(manifest)
        details["analysis"] = {"lint": linted, "score": scored}
        result["analysis"] = (
            linted["clean"] and scored["score"] >= MINIMUM_SCORE and not scored["critical"]
        )
    try:
        result["processing"] = job_roundtrip()
    except (RuntimeError, ValueError, KeyError):
        result["processing"] = False
    return result
