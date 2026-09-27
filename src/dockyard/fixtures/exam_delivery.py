"""A second original application exam: artifact identity, rollout, and durable delivery."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import yaml

from dockyard.fixtures.exam import apply, deployment
from dockyard.fixtures.incident import baseline_path
from dockyard.fixtures.registry_incident import install
from dockyard.probes.kubernetes import get, kubectl
from dockyard.process import run
from dockyard.workspace import atomic_write


def prepare() -> None:
    kubectl(
        "patch",
        "cronjob",
        "dispatch-maintenance",
        "--type=merge",
        "-p",
        json.dumps({"spec": {"suspend": True}}),
    )
    install(broken=False)
    support = os.environ["DOCKYARD_IMAGE"] + "-support"
    built = run(
        ["docker", "build", "-t", support, "-f", "-", "."],
        input_text="FROM "
        + os.environ["DOCKYARD_IMAGE"]
        + "\n"
        + "LABEL io.dockyard.fixture=delivery-support\n"
        + 'LABEL io.dockyard.lab="'
        + os.environ["DOCKYARD_LAB"]
        + '"\n',
        timeout=120,
    )
    if not built.ok:
        raise RuntimeError(built.stderr)
    loaded = run(
        ["kind", "load", "docker-image", support, "--name", os.environ["DOCKYARD_CLUSTER"]],
        timeout=120,
    )
    if not loaded.ok:
        raise RuntimeError(loaded.stderr)
    kubectl("set", "image", "deployment/worker", "worker=" + support)

    version = Path("VERSION").read_text()
    try:
        Path("VERSION").write_text("dispatch-preview-b\n")
        for args in (
            [
                "docker",
                "build",
                "--build-arg",
                "BASE_IMAGE=" + os.environ["DOCKYARD_PYTHON_IMAGE"],
                "-t",
                os.environ["DOCKYARD_IMAGE"] + "-preview",
                ".",
            ],
            [
                "kind",
                "load",
                "docker-image",
                os.environ["DOCKYARD_IMAGE"] + "-preview",
                "--name",
                os.environ["DOCKYARD_CLUSTER"],
            ],
        ):
            result = run(args, timeout=180)
            if not result.ok:
                raise RuntimeError(result.stderr)
    finally:
        Path("VERSION").write_text(version)
    # A preview has its own controller and Service, preserving the stable identity.
    preview = get("deployment", "dispatch")
    preview = {k: preview[k] for k in ("apiVersion", "kind", "spec")}
    preview["metadata"] = {"name": "preview-api", "namespace": "dispatch"}
    preview["spec"]["selector"] = {"matchLabels": {"app": "preview-api"}}
    preview["spec"]["template"]["metadata"] = {"labels": {"app": "preview-api"}}
    preview["spec"]["strategy"] = {
        "type": "RollingUpdate",
        "rollingUpdate": {"maxUnavailable": 1, "maxSurge": 0},
    }
    api = preview["spec"]["template"]["spec"]["containers"][0]
    api["image"] = os.environ["DOCKYARD_IMAGE"] + "-missing-preview"
    api["imagePullPolicy"] = "Never"
    apply(
        preview,
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "preview", "namespace": "dispatch"},
            "spec": {
                "selector": {"app": "dispatch"},
                "ports": [{"port": 8080, "targetPort": 8080}],
            },
        },
    )
    kubectl(
        "set", "env", "deployment/dispatch", "DB_PASSWORD_FILE=/var/run/dispatch/retired-password"
    )
    kubectl(
        "patch",
        "deployment",
        "dispatch",
        "--type=merge",
        "-p",
        json.dumps({"spec": {"template": {"spec": {"automountServiceAccountToken": True}}}}),
    )
    kubectl(
        "patch",
        "deployment",
        "worker",
        "--type=strategic",
        "-p",
        json.dumps(
            {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": "worker",
                                    "resources": {
                                        "requests": {"cpu": "99"},
                                        "limits": {"cpu": "99"},
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        ),
    )
    listener = deployment(
        "report-listener",
        [
            "python",
            "-u",
            "-c",
            "import os,http.server; "
            "http.server.ThreadingHTTPServer(('0.0.0.0',int(os.environ['PORT'])),"
            "http.server.SimpleHTTPRequestHandler).serve_forever()",
        ],
    )
    listener["spec"]["template"]["spec"]["containers"][0]["image"] = support
    listener["spec"]["template"]["spec"]["containers"][0]["env"] = [
        {"name": "PORT", "value": "eight"}
    ]
    apply(
        listener,
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "reports", "namespace": "dispatch"},
            "spec": {
                "selector": {"app": "report-listener"},
                "ports": [{"port": 8080, "targetPort": 8080}],
            },
        },
    )
    metadata = deployment(
        "metadata-reader", ["python", "-m", "http.server", "8080", "--directory", "/metadata"]
    )
    spec = metadata["spec"]["template"]["spec"]
    spec["containers"][0]["image"] = support
    spec["containers"][0]["volumeMounts"] = [{"name": "metadata", "mountPath": "/metadata"}]
    spec["volumes"] = [{"name": "metadata", "configMap": {"name": "release-metadata"}}]
    base = Path("release/base")
    overlay = Path("release/overlays/production")
    base.mkdir(parents=True, exist_ok=True)
    overlay.mkdir(parents=True, exist_ok=True)
    (base / "reader.yaml").write_text(yaml.safe_dump(metadata))
    (base / "kustomization.yaml").write_text(
        yaml.safe_dump(
            {
                "apiVersion": "kustomize.config.k8s.io/v1beta1",
                "kind": "Kustomization",
                "namespace": "dispatch",
                "resources": ["reader.yaml"],
                "configMapGenerator": [
                    {
                        "name": "release-metadata",
                        "literals": ["environment=staging", "release=unapproved"],
                    }
                ],
            }
        )
    )
    (overlay / "kustomization.yaml").write_text(
        yaml.safe_dump(
            {
                "apiVersion": "kustomize.config.k8s.io/v1beta1",
                "kind": "Kustomization",
                "resources": ["../../base"],
            }
        )
    )
    kubectl("apply", "-k", str(overlay))
    archive = deployment(
        "report-cache", ["python", "-c", "import time; time.sleep(86400)"], image=support
    )
    spec = archive["spec"]["template"]["spec"]
    spec["securityContext"] = {"fsGroup": 10001}
    spec["containers"][0]["volumeMounts"] = [{"name": "archive", "mountPath": "/archive"}]
    spec["volumes"] = [{"name": "archive", "persistentVolumeClaim": {"claimName": "report-cache"}}]
    apply(
        {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": "report-cache", "namespace": "dispatch"},
            "spec": {
                "storageClassName": "standard",
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": "128Mi"}},
            },
        },
        archive,
    )
    kubectl("rollout", "status", "deployment/report-cache", "--timeout=120s", timeout=130)
    payload = (
        json.dumps(
            {"release": "dispatch-approved-b", "retention_days": 30, "source": "accepted-delivery"},
            sort_keys=True,
        )
        + "\n"
    )
    Path("report-backup.json").write_text(payload)
    # The learner must restore this independently recorded artifact into the retained claim.
    baseline = json.loads(baseline_path().read_text())
    baseline["report-cache"] = get("pvc", "report-cache")["metadata"]["uid"]
    baseline["report_hash"] = hashlib.sha256(payload.encode()).hexdigest()
    baseline["stable_release"] = version.strip()
    atomic_write(baseline_path(), json.dumps(baseline).encode())
    print("Prepared eight delivery tasks with separate stable and preview paths.")


if __name__ == "__main__":
    prepare()
