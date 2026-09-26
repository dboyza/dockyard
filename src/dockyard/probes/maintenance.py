"""Observe preserved cluster identity, actual upgrades, evictions, and served certificates."""

from __future__ import annotations

import base64
import hashlib
import json
import socket
import ssl
import sys
from contextlib import suppress
from typing import Any

import yaml
from cryptography import x509

from dockyard.native import current
from dockyard.probes.bootstrap import ERRORS
from dockyard.probes.kubernetes import sql
from dockyard.probes.native import workflow
from dockyard.runtimes.linux import LinuxRuntime


def observed(runtime: LinuxRuntime, args: list[str]) -> dict[str, Any]:
    value = runtime.kubectl(args + ["-o", "json"], timeout=20)
    runtime.require(value)
    return dict(json.loads(value.stdout))


def certificate(runtime: LinuxRuntime) -> tuple[int, str]:
    primary = "d" + runtime.lab.id[:10] + "-cp1"
    result = runtime.guest(primary, ["sudo", "cat", "/etc/kubernetes/pki/apiserver.crt"])
    runtime.require(result)
    cert = x509.load_pem_x509_certificate(result.stdout.encode())
    ca = runtime.guest(primary, ["sudo", "cat", "/etc/kubernetes/pki/ca.crt"])
    runtime.require(ca)
    return cert.serial_number, hashlib.sha256(ca.stdout.encode()).hexdigest()


def served_serial(runtime: LinuxRuntime) -> int:
    configuration = yaml.safe_load((runtime.root / "kubeconfig").read_text())
    ca = base64.b64decode(configuration["clusters"][0]["cluster"]["certificate-authority-data"])
    context = ssl.create_default_context(cadata=ca.decode())
    with (
        socket.create_connection(("127.0.0.1", int(runtime.lab.resources["api_port"])), 5) as raw,
        context.wrap_socket(raw, server_hostname="127.0.0.1") as secure,
    ):
        peer = secure.getpeercert(binary_form=True)
    if peer is None:
        raise ValueError("The native endpoint did not present a certificate.")
    return x509.load_der_x509_certificate(peer).serial_number


def maintenance(mode: str) -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(
        ("preserved", "upgrade", "drained", "renewed", "workflow"), False
    )
    details: dict[str, Any] = {}
    result["_details"] = details
    runtime = current()
    baseline = json.loads((runtime.root / "data/maintenance-baseline.json").read_text())
    with suppress(*ERRORS):
        namespace = observed(runtime, ["get", "namespace", "dispatch"])
        nodes = observed(runtime, ["get", "nodes"])["items"]
        identities = {node["metadata"]["name"]: node["metadata"]["uid"] for node in nodes}
        marker = observed(runtime, ["get", "configmap", "maintenance-sentinel", "-n", "default"])
        job_id = baseline["job_id"]
        if len(job_id) != 32 or any(c not in "0123456789abcdef" for c in job_id):
            raise ValueError("The maintenance sentinel has an invalid identity.")
        row = sql(f"SELECT title FROM jobs WHERE id='{job_id}'", workload="statefulset/db").strip()
        result["preserved"] = bool(
            namespace["metadata"]["uid"] == baseline["namespace_uid"]
            and identities == baseline["nodes"]
            and marker["metadata"]["uid"] == baseline["marker_uid"]
            and marker["data"]["marker"] == baseline["marker"]
            and row == "maintenance-preserved"
        )
        details["preserved"] = {
            "namespace_and_nodes_unchanged": identities == baseline["nodes"]
            and namespace["metadata"]["uid"] == baseline["namespace_uid"],
            "persisted_sentinel": row == "maintenance-preserved",
        }
    if mode == "upgrade":
        with suppress(*ERRORS):
            nodes = observed(runtime, ["get", "nodes"])["items"]
            version = runtime.kubectl(["get", "--raw=/version"])
            runtime.require(version)
            actual = json.loads(version.stdout)["gitVersion"]
            components = observed(
                runtime, ["get", "pods", "-n", "kube-system", "-l", "tier=control-plane"]
            )["items"]
            required = {"kube-apiserver", "kube-controller-manager", "kube-scheduler"}
            images = {
                p["metadata"]["labels"].get("component"): p["spec"]["containers"][0]["image"]
                for p in components
            }
            result["upgrade"] = bool(
                baseline["version"] == "v1.34.12"
                and actual == "v1.35.8"
                and len(nodes) == len(baseline["nodes"])
                and all(
                    n["status"]["nodeInfo"]["kubeletVersion"] == "v1.35.8"
                    and not n.get("spec", {}).get("unschedulable", False)
                    and any(
                        c["type"] == "Ready" and c["status"] == "True"
                        for c in n["status"]["conditions"]
                    )
                    for n in nodes
                )
                and all(images.get(name, "").endswith(":v1.35.8") for name in required)
            )
            details["upgrade"] = {
                "api_version": actual,
                "kubelet_versions": [n["status"]["nodeInfo"]["kubeletVersion"] for n in nodes],
                "component_images": images,
            }
    if mode == "drain":
        with suppress(*ERRORS):
            target = "lima-d" + runtime.lab.id[:10] + "-worker2"
            node = observed(runtime, ["get", "node", target])
            pods = observed(
                runtime, ["get", "pods", "-A", "--field-selector=spec.nodeName=" + target]
            )["items"]
            ordinary = [
                p["metadata"]["name"]
                for p in pods
                if not p["metadata"].get("annotations", {}).get("kubernetes.io/config.mirror")
                and not any(
                    o["kind"] == "DaemonSet" for o in p["metadata"].get("ownerReferences", [])
                )
                and p.get("status", {}).get("phase") not in {"Succeeded", "Failed"}
            ]
            deployment = observed(runtime, ["get", "deployment", "dispatch"])
            replicas = deployment.get("status", {}).get("availableReplicas", 0)
            budget = observed(runtime, ["get", "pdb", "dispatch-maintenance"])
            selected = budget["spec"].get("selector", {}).get("matchLabels") == {
                "app": "dispatch",
                "track": "stable",
            }
            protected = (
                budget["spec"].get("minAvailable") in (1, "50%")
                or budget["spec"].get("maxUnavailable") == 1
            )
            result["drained"] = bool(
                node["spec"].get("unschedulable") is True
                and not ordinary
                and deployment["spec"]["replicas"] >= 2
                and replicas >= 2
                and selected
                and protected
            )
            details["drained"] = {
                "target": target,
                "cordoned": node["spec"].get("unschedulable", False),
                "ordinary_pods_remaining": ordinary,
                "available_api_replicas": replicas,
                "budget_protects_one": selected and protected,
            }
    if mode == "certificates":
        with suppress(*ERRORS):
            serial, ca = certificate(runtime)
            served = served_serial(runtime)
            result["renewed"] = bool(
                serial != baseline["serial"] and served == serial and ca == baseline["ca"]
            )
            details["renewed"] = {
                "serial_changed": serial != baseline["serial"],
                "serving_renewed_certificate": served == serial,
                "ca_preserved": ca == baseline["ca"],
            }
    with suppress(*ERRORS):
        result["workflow"] = workflow()
    return result


if __name__ == "__main__":
    print(json.dumps(maintenance(sys.argv[1])))
