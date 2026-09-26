"""Native kubeadm fixtures for lessons that begin with an installed cluster."""

from __future__ import annotations

import ipaddress
import json
import secrets
import shlex
import threading
from typing import Any

import yaml

from dockyard.catalog import CONTENT
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.toolchain import Toolchain
from dockyard.workspace import atomic_write

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


def topology(runtime: LinuxRuntime) -> list[str]:
    names = [entry["name"] for entry in runtime.discover()]
    if len(names) not in {2, 3, 4}:
        raise RuntimeErrorBase(
            "Native bootstrap requires two or three guests, or three control planes and a worker."
        )
    return names


def load_balancer_configuration(names: list[str]) -> str:
    return """global
  maxconn 256
defaults
  mode tcp
  timeout connect 3s
  timeout client 30s
  timeout server 30s
frontend kubernetes
  bind 0.0.0.0:6444
  default_backend control_plane
backend control_plane
  balance roundrobin
  option tcp-check
""" + "".join(
        f"  server cp{index + 1} lima-{name}.internal:6443 check inter 1s fall 2 rise 2\n"
        for index, name in enumerate(names)
    )


def initialize(runtime: LinuxRuntime, cancel: threading.Event, version: str = "1.35.8") -> None:
    names = topology(runtime)
    primary, worker = names[0], names[-1]
    high_availability = len(names) == 4
    certificate_key = None
    if high_availability:
        runtime.require(
            runtime.guest(
                worker,
                ["sudo", "tee", "/etc/haproxy/haproxy.cfg"],
                input_text=load_balancer_configuration(names[:-1]),
                cancel=cancel,
            )
        )
        runtime.require(
            runtime.guest(
                worker, ["sudo", "haproxy", "-c", "-f", "/etc/haproxy/haproxy.cfg"], cancel=cancel
            )
        )
        runtime.require(
            runtime.guest(worker, ["sudo", "systemctl", "restart", "haproxy"], cancel=cancel)
        )
        private = runtime.root / "data"
        private.mkdir(exist_ok=True, mode=0o700)
        path = private / "ha-certificate.key"
        if path.is_symlink():
            raise RuntimeErrorBase(
                "The native certificate upload key must be a private regular file."
            )
        if not path.exists():
            atomic_write(path, secrets.token_hex(32).encode())
        certificate_key = path.read_text().strip()
        if len(certificate_key) != 64 or any(
            value not in "0123456789abcdef" for value in certificate_key
        ):
            raise RuntimeErrorBase("The private certificate upload key is invalid.")
    installed = runtime.guest(
        primary, ["sudo", "test", "-f", "/etc/kubernetes/admin.conf"], cancel=cancel
    )
    if not installed.ok:
        runtime.report("Initializing the native control plane")
        configuration = initialization(runtime, primary, cancel, version)
        command = ["sudo", "kubeadm", "init", "--config=/dev/stdin"]
        if high_availability:
            configuration[0]["certificateKey"] = certificate_key
            configuration[1]["controlPlaneEndpoint"] = "lima-" + worker + ".internal:6444"
            configuration[1]["apiServer"]["certSANs"].append("lima-" + worker + ".internal")
            command.append("--upload-certs")
        runtime.require(
            runtime.guest(
                primary,
                command,
                input_text=yaml.safe_dump_all(configuration),
                timeout=600,
                cancel=cancel,
            )
        )
    elif certificate_key:
        runtime.require(
            runtime.guest(
                primary,
                [
                    "sudo",
                    "kubeadm",
                    "init",
                    "phase",
                    "upload-certs",
                    "--upload-certs",
                    "--certificate-key",
                    certificate_key,
                ],
                timeout=60,
                cancel=cancel,
            )
        )
    runtime.export_kubeconfig(cancel)


def join_configuration(runtime: LinuxRuntime, name: str, cancel: threading.Event) -> dict[str, Any]:
    names = topology(runtime)
    if name not in names[1:]:
        raise RuntimeErrorBase("Join configuration must target another recorded guest in this lab.")
    result = runtime.guest(
        names[0],
        ["sudo", "kubeadm", "token", "create", "--print-join-command", "--ttl=24h"],
        cancel=cancel,
    )
    runtime.require(result)
    parts = shlex.split(result.stdout)
    token = parts[parts.index("--token") + 1]
    ca_hash = parts[parts.index("--discovery-token-ca-cert-hash") + 1]
    runtime.lab.resources["bootstrap_token"] = token
    runtime.save(runtime.lab)
    node_ip = address(runtime, name, cancel)
    configuration: dict[str, Any] = {
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
            "name": "lima-" + name,
            "criSocket": "unix:///run/containerd/containerd.sock",
            "kubeletExtraArgs": [{"name": "node-ip", "value": node_ip}],
        },
    }
    if len(names) == 4 and name != names[-1]:
        configuration["controlPlane"] = {
            "localAPIEndpoint": {"advertiseAddress": node_ip, "bindPort": 6443},
            "certificateKey": (runtime.root / "data/ha-certificate.key").read_text().strip(),
        }
    return configuration


def join(runtime: LinuxRuntime, cancel: threading.Event) -> None:
    for name in topology(runtime)[1:]:
        if runtime.guest(
            name, ["sudo", "test", "-f", "/etc/kubernetes/kubelet.conf"], cancel=cancel
        ).ok:
            continue
        runtime.report("Joining the native node with CA-pinned discovery")
        runtime.require(
            runtime.guest(
                name,
                ["sudo", "kubeadm", "join", "--config=/dev/stdin"],
                input_text=yaml.safe_dump(join_configuration(runtime, name, cancel)),
                timeout=360,
                cancel=cancel,
            )
        )


def spread_dns(runtime: LinuxRuntime, cancel: threading.Event) -> None:
    if len(topology(runtime)) == 4:
        # A control-plane outage must not remove every DNS replica along with it.
        dns = {
            "spec": {
                "replicas": 3,
                "template": {
                    "spec": {
                        "nodeSelector": {
                            "kubernetes.io/os": "linux",
                            "node-role.kubernetes.io/control-plane": "",
                        },
                        "affinity": {
                            "podAntiAffinity": {
                                "requiredDuringSchedulingIgnoredDuringExecution": [
                                    {
                                        "labelSelector": {"matchLabels": {"k8s-app": "kube-dns"}},
                                        "topologyKey": "kubernetes.io/hostname",
                                    }
                                ],
                            },
                        },
                    },
                },
            },
        }
        runtime.require(
            runtime.kubectl(
                [
                    "patch",
                    "deployment",
                    "coredns",
                    "-n",
                    "kube-system",
                    "--type=merge",
                    "-p",
                    json.dumps(dns),
                ],
                timeout=30,
                cancel=cancel,
            )
        )


def network(runtime: LinuxRuntime, cancel: threading.Event) -> None:
    runtime.report("Installing native VXLAN networking and checking DNS readiness")
    runtime.require(
        runtime.kubectl(
            ["apply", "-f", "-"],
            payload=network_manifest(runtime, cancel),
            timeout=120,
            cancel=cancel,
        )
    )
    spread_dns(runtime, cancel)
    for args in (
        ["wait", "--for=condition=Ready", "nodes", "--all", "--timeout=240s"],
        ["rollout", "status", "daemonset/calico-node", "-n", "kube-system", "--timeout=240s"],
        ["rollout", "status", "deployment/coredns", "-n", "kube-system", "--timeout=240s"],
    ):
        runtime.require(runtime.kubectl(args, timeout=250, cancel=cancel))


def prepare(runtime: LinuxRuntime, cancel: threading.Event, version: str = "1.35.8") -> None:
    initialize(runtime, cancel, version)
    join(runtime, cancel)
    network(runtime, cancel)
