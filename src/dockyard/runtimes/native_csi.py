"""A pinned, guest-local CSI reference driver with real controller and node operations."""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any

import yaml

from dockyard.catalog import CONTENT
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.runtimes.native_images import load

NAMESPACE = "dockyard-storage-system"
CONTAINERS = {
    "hostpath": "csi_hostpath",
    "node-driver-registrar": "csi_registrar",
    "liveness-probe": "csi_liveness",
    "csi-attacher": "csi_attacher",
    "csi-provisioner": "csi_provisioner",
    "csi-resizer": "csi_resizer",
}


def manifest(runtime: LinuxRuntime) -> str:
    root = CONTENT / "runtime/csi"
    sources = json.loads((root / "sources.json").read_text())
    for name, expected in sources["files"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise RuntimeErrorBase("The packaged CSI upstream manifest changed identity.")
    objects: list[dict[str, Any]] = [
        {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": NAMESPACE,
                "labels": {
                    "pod-security.kubernetes.io/enforce": "privileged",
                    "io.dockyard.lab": runtime.lab.id,
                },
            },
        }
    ]
    source = list(yaml.safe_load_all((root / "csi-hostpath-plugin.yaml").read_text()))
    account = next(item for item in source if item.get("kind") == "ServiceAccount")
    account["metadata"]["namespace"] = NAMESPACE
    objects.append(account)
    for component in ("external-attacher", "external-provisioner", "external-resizer"):
        for role in yaml.safe_load_all((root / (component + "-rbac.yaml")).read_text()):
            if not role or role.get("kind") not in {"Role", "ClusterRole"}:
                continue
            role["metadata"]["name"] = "dockyard-" + role["metadata"]["name"]
            if role["kind"] == "Role":
                role["metadata"]["namespace"] = NAMESPACE
            objects.append(role)
            metadata = {"name": role["metadata"]["name"]}
            if role["kind"] == "Role":
                metadata["namespace"] = NAMESPACE
            objects.append(
                {
                    "apiVersion": "rbac.authorization.k8s.io/v1",
                    "kind": role["kind"] + "Binding",
                    "metadata": metadata,
                    "roleRef": {
                        "apiGroup": "rbac.authorization.k8s.io",
                        "kind": role["kind"],
                        "name": role["metadata"]["name"],
                    },
                    "subjects": [
                        {
                            "kind": "ServiceAccount",
                            "name": account["metadata"]["name"],
                            "namespace": NAMESPACE,
                        }
                    ],
                }
            )
    objects.extend(yaml.safe_load_all((root / "csi-hostpath-driverinfo.yaml").read_text()))
    plugin = next(item for item in source if item.get("kind") == "StatefulSet")
    plugin["metadata"]["namespace"] = NAMESPACE
    spec = plugin["spec"]["template"]["spec"]
    spec["nodeSelector"] = {"kubernetes.io/hostname": "lima-d" + runtime.lab.id[:10] + "-worker"}
    spec["containers"] = [
        container for container in spec["containers"] if container["name"] in CONTAINERS
    ]
    for container in spec["containers"]:
        key = CONTAINERS[container["name"]]
        container["image"] = runtime.env["DOCKYARD_" + key.upper() + "_LOCAL_IMAGE"]
        container["imagePullPolicy"] = "Never"
        container["resources"] = {
            "requests": {"cpu": "10m", "memory": "24Mi"},
            "limits": {"cpu": "200m", "memory": "192Mi"},
        }
    objects.append(plugin)
    for item in objects:
        item["metadata"].setdefault("labels", {})["io.dockyard.lab"] = runtime.lab.id
    return yaml.safe_dump_all(objects)


def prepare(runtime: LinuxRuntime, cancel: threading.Event) -> None:
    images = json.loads((CONTENT / "compatibility.json").read_text())["images"]
    for key in CONTAINERS.values():
        load(runtime, images[key], cancel)
    runtime.require(
        runtime.kubectl(["apply", "-f", "-"], payload=manifest(runtime), timeout=90, cancel=cancel)
    )
    runtime.require(
        runtime.kubectl(
            [
                "rollout",
                "status",
                "statefulset/csi-hostpathplugin",
                "-n",
                NAMESPACE,
                "--timeout=180s",
            ],
            timeout=190,
            cancel=cancel,
        )
    )
