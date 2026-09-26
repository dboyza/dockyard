"""Native kubeadm fixtures for lessons that begin with an installed cluster."""

from __future__ import annotations

import ipaddress
import json
import shlex
import threading
from typing import Any

import yaml

from dockyard.catalog import CONTENT
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.toolchain import Toolchain

POD_CIDR = "10.244.0.0/16"


def address(runtime: LinuxRuntime, name: str, cancel: threading.Event) -> str:
    result = runtime.guest(name, ["hostname", "-I"], cancel=cancel)
    runtime.require(result)
    addresses = [ipaddress.ip_address(value) for value in result.stdout.split()]
    network = ipaddress.ip_network("192.168.104.0/24")
    candidates = [str(value) for value in addresses if value in network]
    if len(candidates) != 1:
        raise RuntimeErrorBase("The native guest does not have one expected private node address.")
    return candidates[0]


def initialization(
    runtime: LinuxRuntime, name: str, cancel: threading.Event, version: str
) -> list[dict[str, Any]]:
    if version not in {"1.34.12", "1.35.8"}:
        raise RuntimeErrorBase("The native cluster version is not in the verified matrix.")
    node_ip = address(runtime, name, cancel)
    return [
        {
            "apiVersion": "kubeadm.k8s.io/v1beta4",
            "kind": "InitConfiguration",
            "localAPIEndpoint": {"advertiseAddress": node_ip, "bindPort": 6443},
            "nodeRegistration": {
                "name": "lima-" + name,
                "criSocket": "unix:///run/containerd/containerd.sock",
                "kubeletExtraArgs": [{"name": "node-ip", "value": node_ip}],
            },
        },
        {
            "apiVersion": "kubeadm.k8s.io/v1beta4",
            "kind": "ClusterConfiguration",
            "kubernetesVersion": "v" + version,
            "controlPlaneEndpoint": "lima-" + name + ".internal:6443",
            "apiServer": {"certSANs": ["127.0.0.1", "lima-" + name + ".internal"]},
            "networking": {"podSubnet": POD_CIDR},
        },
    ]


def network_manifest(runtime: LinuxRuntime, cancel: threading.Event) -> str:
    path = Toolchain(runtime.tools).ensure("calico", cancel, runtime.report)
    objects = list(yaml.safe_load_all(path.read_text()))
    images = json.loads((CONTENT / "compatibility.json").read_text())["images"]
    for item in objects:
        if item.get("kind") == "ConfigMap" and item["metadata"]["name"] == "calico-config":
            item["data"]["calico_backend"] = "vxlan"
        spec = item.get("spec", {}).get("template", {}).get("spec", {})
        for container in spec.get("initContainers", []) + spec.get("containers", []):
            for key, upstream in (
                ("calico_cni", "cni"),
                ("calico_node", "node"),
                ("calico_controllers", "kube-controllers"),
            ):
                if container.get("image") == "quay.io/calico/" + upstream + ":v3.32.2":
                    container["image"] = images[key]
            if container["name"] != "calico-node":
                continue
            overrides = {
                "CALICO_IPV4POOL_IPIP": "Never",
                "CALICO_IPV4POOL_VXLAN": "Always",
                "CALICO_IPV4POOL_CIDR": POD_CIDR,
                "CLUSTER_TYPE": "k8s",
                "IP_AUTODETECTION_METHOD": "kubernetes-internal-ip",
            }
            container["env"] = [
                entry for entry in container.get("env", []) if entry["name"] not in overrides
            ] + [{"name": key, "value": value} for key, value in overrides.items()]
            for probe in ("readinessProbe", "livenessProbe"):
                if probe in container:
                    command = container[probe]["exec"]["command"]
                    container[probe]["exec"]["command"] = [
                        value for value in command if not value.startswith("-bird-")
                    ]
    return yaml.safe_dump_all(objects)


def prepare(runtime: LinuxRuntime, cancel: threading.Event, version: str = "1.35.8") -> None:
    entries = runtime.discover()
    if len(entries) != 2:
        raise RuntimeErrorBase(
            "This native bootstrap fixture requires one control plane and worker."
        )
    primary, worker = entries[0]["name"], entries[1]["name"]
    installed = runtime.guest(
        primary, ["sudo", "test", "-f", "/etc/kubernetes/admin.conf"], cancel=cancel
    )
    if not installed.ok:
        runtime.report("Initializing the native control plane")
        runtime.require(
            runtime.guest(
                primary,
                ["sudo", "kubeadm", "init", "--config=/dev/stdin"],
                input_text=yaml.safe_dump_all(initialization(runtime, primary, cancel, version)),
                timeout=600,
                cancel=cancel,
            )
        )
    installed = runtime.guest(
        worker, ["sudo", "test", "-f", "/etc/kubernetes/kubelet.conf"], cancel=cancel
    )
    if not installed.ok:
        runtime.report("Joining the native worker with CA-pinned discovery")
        result = runtime.guest(
            primary,
            ["sudo", "kubeadm", "token", "create", "--print-join-command", "--ttl=24h"],
            cancel=cancel,
        )
        runtime.require(result)
        parts = shlex.split(result.stdout)
        token = parts[parts.index("--token") + 1]
        ca_hash = parts[parts.index("--discovery-token-ca-cert-hash") + 1]
        runtime.lab.resources["bootstrap_token"] = token
        runtime.save(runtime.lab)
        node_ip = address(runtime, worker, cancel)
        configuration = {
            "apiVersion": "kubeadm.k8s.io/v1beta4",
            "kind": "JoinConfiguration",
            "discovery": {
                "bootstrapToken": {
                    "apiServerEndpoint": parts[2],
                    "token": token,
                    "caCertHashes": [ca_hash],
                }
            },
            "nodeRegistration": {
                "name": "lima-" + worker,
                "criSocket": "unix:///run/containerd/containerd.sock",
                "kubeletExtraArgs": [{"name": "node-ip", "value": node_ip}],
            },
        }
        runtime.require(
            runtime.guest(
                worker,
                ["sudo", "kubeadm", "join", "--config=/dev/stdin"],
                input_text=yaml.safe_dump(configuration),
                timeout=300,
                cancel=cancel,
            )
        )
    runtime.export_kubeconfig(cancel)
    runtime.report("Installing native VXLAN networking and checking DNS readiness")
    runtime.require(
        runtime.kubectl(
            ["apply", "-f", "-"],
            payload=network_manifest(runtime, cancel),
            timeout=120,
            cancel=cancel,
        )
    )
    for args in (
        ["wait", "--for=condition=Ready", "nodes", "--all", "--timeout=240s"],
        ["rollout", "status", "daemonset/calico-node", "-n", "kube-system", "--timeout=240s"],
        ["rollout", "status", "deployment/coredns", "-n", "kube-system", "--timeout=240s"],
    ):
        runtime.require(runtime.kubectl(args, timeout=250, cancel=cancel))
