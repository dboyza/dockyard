"""Pinned, cluster-local routing controllers with no host-wide cluster discovery."""

from __future__ import annotations

import ipaddress
import json
import threading
import time
from typing import TYPE_CHECKING, Any

import yaml

from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.toolchain import Toolchain

if TYPE_CHECKING:
    from dockyard.runtimes.kubernetes import KubernetesRuntime


def install(runtime: KubernetesRuntime, capabilities: list[str], cancel: threading.Event) -> None:
    def report(message: str) -> None:
        runtime.lab.resources["stage"] = message
        runtime.save(runtime.lab)

    def apply(documents: list[dict[str, Any]]) -> None:
        runtime.docker.require(
            runtime.kubectl(
                ["apply", "-f", "-"],
                payload=yaml.safe_dump_all(documents),
                timeout=90,
                cancel=cancel,
            )
        )

    toolchain = Toolchain(runtime.tools)
    if "loadbalancer" in capabilities:
        report("Preparing the cluster-local load balancer")
        source = toolchain.ensure("metallb", cancel, report)
        manifest = source.read_text()
        for component in ("controller", "speaker"):
            manifest = manifest.replace(
                f"quay.io/metallb/{component}:v0.16.1",
                runtime.env[f"DOCKYARD_METALLB_{component.upper()}_LOCAL_IMAGE"],
            )
        runtime.docker.require(
            runtime.kubectl(
                [
                    "apply",
                    "--server-side",
                    "-f",
                    "-",
                ],
                payload=manifest,
                timeout=90,
                cancel=cancel,
            )
        )
        runtime.docker.require(
            runtime.kubectl(
                [
                    "label",
                    "nodes",
                    "--all",
                    "node.kubernetes.io/exclude-from-external-load-balancers-",
                ],
                cancel=cancel,
            )
        )
        for kind, name in (("deployment", "controller"), ("daemonset", "speaker")):
            runtime.docker.require(
                runtime.kubectl(
                    [
                        "rollout",
                        "status",
                        f"{kind}/{name}",
                        "-n",
                        "metallb-system",
                        "--timeout=120s",
                    ],
                    timeout=130,
                    cancel=cancel,
                )
            )
        network = runtime.docker.inspect("network", runtime.lab.resources["kind_network"])
        if network is None:
            raise RuntimeErrorBase("The private load balancer network is missing.")
        ipv4 = next(
            ipaddress.ip_network(item["Subnet"])
            for item in network["IPAM"]["Config"]
            if ":" not in item["Subnet"]
        )
        if ipv4.num_addresses < 128:
            raise RuntimeErrorBase(
                "The private network is too small for its practice address pool."
            )
        pool = f"{ipv4.broadcast_address - 32}-{ipv4.broadcast_address - 17}"
        configuration = [
            {
                "apiVersion": "metallb.io/v1beta1",
                "kind": "IPAddressPool",
                "metadata": {"name": "dockyard", "namespace": "metallb-system"},
                "spec": {"addresses": [pool]},
            },
            {
                "apiVersion": "metallb.io/v1beta1",
                "kind": "L2Advertisement",
                "metadata": {"name": "dockyard", "namespace": "metallb-system"},
                "spec": {"ipAddressPools": ["dockyard"]},
            },
        ]
        deadline = time.monotonic() + 45
        while True:
            result = runtime.kubectl(
                ["apply", "-f", "-"], payload=yaml.safe_dump_all(configuration), cancel=cancel
            )
            if result.ok:
                break
            if cancel.wait(0.5) or time.monotonic() > deadline:
                runtime.docker.require(result)
        runtime.lab.resources["loadbalancer_pool"] = pool
        runtime.save(runtime.lab)
    if "routing" not in capabilities:
        return
    report("Preparing ingress and Gateway API routing")
    gateway = toolchain.ensure("gateway", cancel, report)
    rbac = toolchain.ensure("traefik-rbac", cancel, report)
    runtime.docker.require(
        runtime.kubectl(
            [
                "apply",
                "--server-side",
                "-f",
                str(gateway),
            ],
            timeout=90,
            cancel=cancel,
        )
    )
    rules = yaml.safe_load_all(rbac.read_text())
    role = next(rules)
    role["metadata"]["name"] = "dockyard-routing"
    role["rules"] += [
        {"apiGroups": [""], "resources": ["nodes"], "verbs": ["get", "list", "watch"]},
        {
            "apiGroups": ["networking.k8s.io"],
            "resources": ["ingresses", "ingressclasses"],
            "verbs": ["get", "list", "watch"],
        },
        {
            "apiGroups": ["networking.k8s.io"],
            "resources": ["ingresses/status"],
            "verbs": ["update"],
        },
    ]
    namespace = "dockyard-routing"
    documents = [
        {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": namespace}},
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": "traefik", "namespace": namespace},
        },
        role,
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "ClusterRoleBinding",
            "metadata": {"name": "dockyard-routing"},
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "ClusterRole",
                "name": "dockyard-routing",
            },
            "subjects": [{"kind": "ServiceAccount", "name": "traefik", "namespace": namespace}],
        },
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "IngressClass",
            "metadata": {"name": "traefik"},
            "spec": {"controller": "traefik.io/ingress-controller"},
        },
        {
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "GatewayClass",
            "metadata": {"name": "traefik"},
            "spec": {"controllerName": "traefik.io/gateway-controller"},
        },
        {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "traefik", "namespace": namespace},
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "traefik"}},
                "template": {
                    "metadata": {"labels": {"app": "traefik"}},
                    "spec": {
                        "serviceAccountName": "traefik",
                        "containers": [
                            {
                                "name": "traefik",
                                "image": runtime.env["DOCKYARD_TRAEFIK_LOCAL_IMAGE"],
                                "imagePullPolicy": "Never",
                                "args": [
                                    "--entrypoints.web.address=:8080",
                                    "--entrypoints.websecure.address=:8443",
                                    "--providers.kubernetesingress=true",
                                    "--providers.kubernetesgateway=true",
                                    "--providers.kubernetesingress.ingressclass=traefik",
                                    "--ping=true",
                                    "--entrypoints.traefik.address=:9000",
                                    "--global.checknewversion=false",
                                    "--global.sendanonymoususage=false",
                                ],
                                "ports": [
                                    {"name": "web", "containerPort": 8080},
                                    {"name": "websecure", "containerPort": 8443},
                                ],
                                "readinessProbe": {"httpGet": {"path": "/ping", "port": 9000}},
                                "resources": {
                                    "requests": {"cpu": "50m", "memory": "64Mi"},
                                    "limits": {"cpu": "500m", "memory": "256Mi"},
                                },
                                "securityContext": {
                                    "runAsNonRoot": True,
                                    "runAsUser": 65532,
                                    "allowPrivilegeEscalation": False,
                                    "capabilities": {"drop": ["ALL"]},
                                },
                            }
                        ],
                    },
                },
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "traefik", "namespace": namespace},
            "spec": {
                "type": "NodePort",
                "selector": {"app": "traefik"},
                "ports": [
                    {"name": "web", "port": 80, "targetPort": "web", "nodePort": 30080},
                    {
                        "name": "websecure",
                        "port": 443,
                        "targetPort": "websecure",
                        "nodePort": 30443,
                    },
                ],
            },
        },
    ]
    apply(documents)
    runtime.docker.require(
        runtime.kubectl(
            [
                "rollout",
                "status",
                "deployment/traefik",
                "-n",
                namespace,
                "--timeout=120s",
            ],
            timeout=130,
            cancel=cancel,
        )
    )
    runtime.lab.resources["routing"] = json.dumps({"ingress": "traefik", "gateway": "traefik"})
    runtime.save(runtime.lab)
