"""Local metrics with verified kubelet and aggregation TLS identities."""

from __future__ import annotations

import base64
import json
import threading
import time
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import yaml
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.toolchain import Toolchain

if TYPE_CHECKING:
    from dockyard.runtimes.kubernetes import KubernetesRuntime


def valid_serving_request(request: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> bool:
    spec = request["spec"]
    username = spec.get("username", "")
    name = username.removeprefix("system:node:")
    if name not in nodes or username != f"system:node:{name}":
        return False
    usages = set(spec.get("usages", []))
    if spec.get("signerName") != "kubernetes.io/kubelet-serving" or not (
        "server auth" in usages
        and usages <= {"server auth", "digital signature", "key encipherment"}
    ):
        return False
    try:
        csr = x509.load_pem_x509_csr(base64.b64decode(spec["request"], validate=True))
        subject = csr.subject
        names = subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        organizations = subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        if not (
            csr.is_signature_valid
            and len(subject) == 2
            and len(names) == len(organizations) == 1
            and names[0].value == username
            and organizations[0].value == "system:nodes"
        ):
            return False
        san = csr.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        allowed_ips = {
            address["address"]
            for address in nodes[name]["status"]["addresses"]
            if address["type"] in {"InternalIP", "ExternalIP"}
        }
        allowed_dns = {name} | {
            address["address"]
            for address in nodes[name]["status"]["addresses"]
            if address["type"] in {"Hostname", "InternalDNS", "ExternalDNS"}
        }
        ips = {str(value) for value in san.get_values_for_type(x509.IPAddress)}
        dns = set(san.get_values_for_type(x509.DNSName))
        return bool(
            ips and ips <= allowed_ips and dns <= allowed_dns and len(san) == len(ips) + len(dns)
        )
    except (ValueError, KeyError, x509.ExtensionNotFound, x509.DuplicateExtension):
        return False


def approve_owned_kubelets(runtime: KubernetesRuntime, cancel: threading.Event) -> None:
    owned = {entry["name"] for entry in runtime.discover() if runtime.verify(entry) is not None}
    deadline = time.monotonic() + 90
    approved: set[str] = set()
    while time.monotonic() < deadline:
        node_result = runtime.kubectl(["get", "nodes", "-o", "json"], cancel=cancel)
        runtime.docker.require(node_result)
        nodes = {
            item["metadata"]["name"]: item
            for item in json.loads(node_result.stdout)["items"]
            if item["metadata"]["name"] in owned
        }
        result = runtime.kubectl(["get", "csr", "-o", "json"], cancel=cancel)
        runtime.docker.require(result)
        for request in json.loads(result.stdout)["items"]:
            if not valid_serving_request(request, nodes):
                continue
            conditions = request.get("status", {}).get("conditions", [])
            if any(c["type"] == "Denied" for c in conditions):
                continue
            name = request["spec"]["username"].removeprefix("system:node:")
            if not any(c["type"] == "Approved" for c in conditions):
                runtime.docker.require(
                    runtime.kubectl(
                        ["certificate", "approve", request["metadata"]["name"]],
                        cancel=cancel,
                    )
                )
            if request.get("status", {}).get("certificate"):
                approved.add(name)
        if approved == owned and owned:
            return
        if cancel.wait(0.5):
            raise RuntimeErrorBase("Metrics preparation canceled.")
    raise RuntimeErrorBase("Owned kubelet serving certificate requests did not become ready.")


def serving_identity() -> tuple[str, str, str]:
    """Return a dedicated CA, server certificate, and key without touching host trust."""
    now = datetime.now(UTC)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Dockyard metrics CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(ca_key, hashes.SHA256())
    )
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "metrics-server.kube-system.svc")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(ca_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("metrics-server.kube-system.svc"),
                    x509.DNSName("metrics-server.kube-system.svc.cluster.local"),
                ]
            ),
            critical=False,
        )
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    return (
        base64.b64encode(ca.public_bytes(serialization.Encoding.PEM)).decode(),
        base64.b64encode(cert.public_bytes(serialization.Encoding.PEM)).decode(),
        base64.b64encode(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        ).decode(),
    )


def install(runtime: KubernetesRuntime, cancel: threading.Event) -> None:
    def report(message: str) -> None:
        runtime.lab.resources["stage"] = message
        runtime.save(runtime.lab)

    report("Verifying owned kubelet serving identities")
    approve_owned_kubelets(runtime, cancel)
    report("Preparing metrics with verified TLS")
    source = Toolchain(runtime.tools).ensure("metrics-server", cancel, report)
    documents = list(yaml.safe_load_all(source.read_text()))
    ca, certificate, key = serving_identity()
    documents.insert(
        0,
        {
            "apiVersion": "v1",
            "kind": "Secret",
            "type": "kubernetes.io/tls",
            "metadata": {"name": "dockyard-metrics-tls", "namespace": "kube-system"},
            "data": {"tls.crt": certificate, "tls.key": key},
        },
    )
    for document in documents:
        if document["kind"] == "APIService":
            document["spec"].pop("insecureSkipTLSVerify", None)
            document["spec"]["caBundle"] = ca
        if document["kind"] == "Deployment":
            spec = document["spec"]["template"]["spec"]
            container = spec["containers"][0]
            container["image"] = runtime.env["DOCKYARD_METRICS_SERVER_LOCAL_IMAGE"]
            container["imagePullPolicy"] = "Never"
            container["args"] += [
                "--kubelet-certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                "--tls-cert-file=/var/run/metrics-tls/tls.crt",
                "--tls-private-key-file=/var/run/metrics-tls/tls.key",
            ]
            container.setdefault("volumeMounts", []).append(
                {
                    "name": "serving-tls",
                    "mountPath": "/var/run/metrics-tls",
                    "readOnly": True,
                }
            )
            spec.setdefault("volumes", []).append(
                {
                    "name": "serving-tls",
                    "secret": {"secretName": "dockyard-metrics-tls"},
                }
            )
    runtime.docker.require(
        runtime.kubectl(
            ["apply", "-f", "-"],
            payload=yaml.safe_dump_all(documents),
            timeout=90,
            cancel=cancel,
        )
    )
    runtime.docker.require(
        runtime.kubectl(
            [
                "rollout",
                "status",
                "deployment/metrics-server",
                "-n",
                "kube-system",
                "--timeout=120s",
            ],
            timeout=130,
            cancel=cancel,
        )
    )
    runtime.docker.require(
        runtime.kubectl(
            [
                "wait",
                "--for=condition=Available",
                "apiservice/v1beta1.metrics.k8s.io",
                "--timeout=90s",
            ],
            timeout=100,
            cancel=cancel,
        )
    )
