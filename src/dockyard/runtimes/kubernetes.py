"""Private kind clusters, explicit node identities, and observed API health."""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from dockyard.models import Lab
from dockyard.process import ProcessResult, run
from dockyard.runtimes.docker import DockerRuntime, RuntimeErrorBase
from dockyard.toolchain import Toolchain
from dockyard.workspace import atomic_write

CLUSTER_LABEL = "io.x-k8s.kind.cluster"


class KubernetesRuntime:
    def __init__(self, lab: Lab, env: dict[str, str], save: Callable[[Lab], None], tools: Path):
        self.lab, self.env, self.save, self.tools = lab, env, save, tools
        self.docker = DockerRuntime(lab, env, save)
        self.name = f"dockyard-{lab.id[:12]}"
        self.root = Path(lab.workspace).parent

    def kubectl(
        self,
        args: list[str],
        *,
        timeout: float = 30,
        cancel: threading.Event | None = None,
        payload: str | None = None,
        output_limit: int = 1_000_000,
    ) -> ProcessResult:
        self.verify_kubeconfig()
        return run(
            [
                str(self.tools / "bin/kubectl"),
                "--kubeconfig",
                self.env["KUBECONFIG"],
                "--request-timeout=15s",
                *args,
            ],
            env=self.env,
            timeout=timeout,
            cancel=cancel,
            input_text=payload,
            output_limit=output_limit,
        )

    def config_identity(self) -> str:
        path = Path(self.env["KUBECONFIG"])
        if path.is_symlink() or not path.is_file():
            raise RuntimeErrorBase("The private kubeconfig is missing or is a symbolic link.")
        config = yaml.safe_load(path.read_text())
        clusters, users = config.get("clusters", []), config.get("users", [])
        if len(clusters) != 1 or len(users) != 1:
            raise RuntimeErrorBase("The private kubeconfig must contain exactly one lab identity.")
        cluster, user = clusters[0]["cluster"], users[0]["user"]
        endpoint = urlparse(cluster.get("server", ""))
        if (
            endpoint.scheme != "https"
            or endpoint.hostname != "127.0.0.1"
            or set(cluster) != {"server", "certificate-authority-data"}
            or set(user) != {"client-certificate-data", "client-key-data"}
        ):
            raise RuntimeErrorBase("The lab kubeconfig changed its local authentication boundary.")
        return hashlib.sha256(json.dumps([clusters, users], sort_keys=True).encode()).hexdigest()

    def verify_kubeconfig(self) -> None:
        expected = self.lab.resources.get("kubeconfig_identity")
        if not expected or self.config_identity() != expected:
            raise RuntimeErrorBase("The kubeconfig no longer matches this recorded lab cluster.")

    def discover(self) -> list[dict[str, str]]:
        inventory: list[dict[str, str]] = json.loads(self.lab.resources.get("kind_inventory", "[]"))
        intent = json.loads(self.lab.resources.get("kind_intent", "[]"))
        result = self.docker.command(
            [
                "container",
                "ls",
                "--all",
                "--quiet",
                "--filter",
                f"label={CLUSTER_LABEL}={self.name}",
            ]
        )
        self.docker.require(result)
        for identity in result.stdout.split():
            resource = self.docker.inspect("container", identity)
            if resource is None:
                continue
            created = self.docker.created(resource)
            name = str(resource["Name"]).lstrip("/")
            labels = self.docker.labels("container", resource)
            if (
                name not in intent
                or labels.get(CLUSTER_LABEL) != self.name
                or datetime.fromisoformat(created.replace("Z", "+00:00"))
                < datetime.fromisoformat(self.lab.created_at)
            ):
                raise RuntimeErrorBase("An unrecognized cluster node was preserved.")
            entry = {"id": str(resource["Id"]), "created": created, "name": name}
            if entry not in inventory:
                inventory.append(entry)
        self.lab.resources["kind_inventory"] = json.dumps(inventory)
        self.save(self.lab)
        return inventory

    def verify(self, entry: dict[str, str]) -> dict[str, Any] | None:
        resource = self.docker.inspect("container", entry["id"])
        if resource is None:
            return None
        if (
            resource["Id"] != entry["id"]
            or self.docker.created(resource) != entry["created"]
            or str(resource["Name"]).lstrip("/") != entry["name"]
            or self.docker.labels("container", resource).get(CLUSTER_LABEL) != self.name
        ):
            raise RuntimeErrorBase("A cluster node changed identity; it was preserved.")
        return resource

    def load_image(self, name: str, cancel: threading.Event) -> str:
        image = self.env[f"DOCKYARD_{name.upper()}_IMAGE"]
        local = self.env[f"DOCKYARD_{name.upper()}_LOCAL_IMAGE"]
        if not self.docker.command(["image", "inspect", image]).ok:
            self.docker.require(self.docker.command(["pull", image], timeout=600, cancel=cancel))
        self.docker.require(self.docker.command(["tag", image, local], cancel=cancel))
        archive = self.root / "dependency-image.tar"
        try:
            self.docker.require(
                self.docker.command(
                    [
                        "image",
                        "save",
                        "--platform=linux/arm64",
                        "--output",
                        str(archive),
                        local,
                    ],
                    timeout=180,
                    cancel=cancel,
                )
            )
            self.docker.require(
                run(
                    [
                        str(self.tools / "bin/kind"),
                        "load",
                        "image-archive",
                        str(archive),
                        "--name",
                        self.name,
                    ],
                    env=self.env,
                    timeout=180,
                    cancel=cancel,
                )
            )
        finally:
            archive.unlink(missing_ok=True)
        return local

    def prepare(
        self,
        nodes: int,
        images: list[str],
        cancel: threading.Event,
        capabilities: list[str] | None = None,
    ) -> None:
        def report(message: str) -> None:
            self.lab.resources["stage"] = message
            self.save(self.lab)

        toolchain = Toolchain(self.tools)
        for tool in ("kind", "kubectl", "calico"):
            toolchain.ensure(tool, cancel, report)
        if capabilities and "helm" in capabilities:
            toolchain.ensure("helm", cancel, report)
        inventory = self.discover()
        existing = [entry for entry in inventory if self.verify(entry) is not None]
        if existing and self.lab.resources.get("cluster_ready") == "true":
            self.change("resume", cancel)
            return
        if existing:
            self.change("clean", cancel)
        capacity = self.docker.command(["info", "--format", "{{.MemTotal}}"])
        self.docker.require(capacity)
        required_mib = 2560 + (nodes - 1) * 1536 + 1024
        if int(capacity.stdout.strip()) < required_mib * 1024**2:
            raise RuntimeErrorBase(
                f"This {nodes}-node lab needs at least {required_mib / 1024:g} GiB "
                "allocated to Docker. Dockyard has not changed your Docker settings."
            )
        if shutil.disk_usage(self.root).free < 10 * 1024**3:
            raise RuntimeErrorBase("Free at least 10 GiB of disk before creating this cluster.")
        network = self.env["DOCKYARD_NETWORK"]
        found = self.docker.inspect("network", network)
        if (
            found is not None
            and self.docker.labels("network", found).get("io.dockyard.lab") != self.lab.id
        ):
            raise RuntimeErrorBase("The requested network name belongs to another resource.")
        if found is None:
            self.docker.require(
                self.docker.command(
                    [
                        "network",
                        "create",
                        "--label",
                        f"io.dockyard.lab={self.lab.id}",
                        network,
                    ],
                    cancel=cancel,
                )
            )
        self.docker.discover()
        self.lab.resources["kind_network"] = network
        self.env["KIND_EXPERIMENTAL_DOCKER_NETWORK"] = network
        names = [self.name + "-control-plane"]
        names += [self.name + "-worker" + (str(i) if i > 1 else "") for i in range(1, nodes)]
        self.lab.resources["kind_intent"] = json.dumps(names)
        self.save(self.lab)
        configuration: dict[str, Any] = {
            "kind": "Cluster",
            "apiVersion": "kind.x-k8s.io/v1alpha4",
            "networking": {
                "apiServerAddress": "127.0.0.1",
                "disableDefaultCNI": True,
                "podSubnet": "192.168.0.0/16",
            },
            "nodes": [
                {
                    "role": "control-plane",
                    "extraPortMappings": [
                        {
                            "containerPort": 30080,
                            "hostPort": int(self.lab.resources["port"]),
                            "listenAddress": "127.0.0.1",
                            "protocol": "TCP",
                        },
                        {
                            "containerPort": 30443,
                            "hostPort": int(self.lab.resources["registry_port"]),
                            "listenAddress": "127.0.0.1",
                            "protocol": "TCP",
                        },
                    ],
                }
            ]
            + [{"role": "worker"} for _ in range(nodes - 1)],
        }
        if capabilities and "metrics" in capabilities:
            configuration["kubeadmConfigPatches"] = [
                yaml.safe_dump(
                    {
                        "apiVersion": "kubelet.config.k8s.io/v1beta1",
                        "kind": "KubeletConfiguration",
                        "serverTLSBootstrap": True,
                    }
                )
            ]
        atomic_write(self.root / "kind.yaml", yaml.safe_dump(configuration).encode())
        report("Creating a private Kubernetes cluster")
        try:
            result = run(
                [
                    str(self.tools / "bin/kind"),
                    "create",
                    "cluster",
                    "--name",
                    self.name,
                    "--image",
                    self.env["DOCKYARD_KIND_IMAGE"],
                    "--config",
                    str(self.root / "kind.yaml"),
                    "--kubeconfig",
                    self.env["KUBECONFIG"],
                    "--retain",
                    "--wait",
                    "0s",
                ],
                env=self.env,
                timeout=420,
                cancel=cancel,
            )
        finally:
            self.discover()
        self.docker.require(result)
        Path(self.env["KUBECONFIG"]).chmod(0o600)
        self.lab.resources["kubeconfig_identity"] = self.config_identity()
        self.save(self.lab)
        for entry in self.discover():
            if self.verify(entry):
                memory = "2560m" if entry["name"].endswith("-control-plane") else "1536m"
                self.docker.require(
                    self.docker.command(
                        [
                            "update",
                            "--memory",
                            memory,
                            "--memory-swap",
                            memory,
                            "--cpus",
                            "2",
                            entry["id"],
                        ],
                        cancel=cancel,
                    )
                )
        report("Installing the network policy capable CNI")
        manifest = (self.tools / "downloads/calico-v3.32.2.yaml").read_text()
        for name, upstream in (
            ("calico_cni", "cni"),
            ("calico_node", "node"),
            ("calico_controllers", "kube-controllers"),
        ):
            local = self.load_image(name, cancel)
            manifest = manifest.replace(f"quay.io/calico/{upstream}:v3.32.2", local)
        self.docker.require(
            self.kubectl(
                [
                    "apply",
                    "-f",
                    "-",
                ],
                payload=manifest,
                timeout=90,
                cancel=cancel,
            )
        )
        self.wait_ready(cancel)
        for name in images:
            if name not in {"python", "kind"}:
                report(f"Loading the cached {name} dependency")
                self.load_image(name, cancel)
        for namespace in ("dispatch", "dockyard-observer"):
            self.docker.require(
                self.kubectl(
                    ["apply", "-f", "-"],
                    payload=json.dumps(
                        {
                            "apiVersion": "v1",
                            "kind": "Namespace",
                            "metadata": {
                                "name": namespace,
                                "labels": {"io.dockyard.lab": self.lab.id},
                            },
                        }
                    ),
                    cancel=cancel,
                )
            )
        self.docker.require(
            self.kubectl(
                [
                    "config",
                    "set-context",
                    "--current",
                    "--namespace=dispatch",
                ],
                cancel=cancel,
            )
        )
        if capabilities and set(capabilities) & {"routing", "loadbalancer"}:
            from dockyard.runtimes.routing import install

            install(self, capabilities, cancel)
        if capabilities and "metrics" in capabilities:
            from dockyard.runtimes.metrics import install as install_metrics

            install_metrics(self, cancel)
        self.lab.resources["cluster_capabilities"] = json.dumps(capabilities or [])
        self.lab.resources["cluster_ready"] = "true"
        report("Cluster ready; preparing the exercise")

    def wait_ready(self, cancel: threading.Event) -> None:
        # On restart the listener can precede API readiness and RBAC informer sync.
        deadline = time.monotonic() + 90
        while True:
            ready = self.health(cancel)
            access = self.kubectl(["get", "nodes", "-o", "name"], cancel=cancel)
            if ready.ok and access.ok:
                break
            if cancel.wait(0.5) or time.monotonic() >= deadline:
                self.docker.require(ready if not ready.ok else access)
                raise RuntimeErrorBase("Cluster startup was canceled.")
        self.docker.require(
            self.kubectl(
                [
                    "wait",
                    "--for=condition=Ready",
                    "node",
                    "--all",
                    "--timeout=240s",
                ],
                timeout=250,
                cancel=cancel,
            )
        )
        self.docker.require(
            self.kubectl(
                [
                    "rollout",
                    "status",
                    "daemonset/calico-node",
                    "-n",
                    "kube-system",
                    "--timeout=180s",
                ],
                timeout=190,
                cancel=cancel,
            )
        )
        self.docker.require(
            self.kubectl(
                [
                    "rollout",
                    "status",
                    "deployment/coredns",
                    "-n",
                    "kube-system",
                    "--timeout=120s",
                ],
                timeout=130,
                cancel=cancel,
            )
        )

    def health(self, cancel: threading.Event) -> ProcessResult:
        return self.kubectl(["get", "--raw=/readyz"], timeout=20, cancel=cancel)

    def change(self, action: str, cancel: threading.Event) -> None:
        for entry in self.discover():
            if cancel.is_set():
                raise RuntimeErrorBase("Cluster operation canceled; remaining nodes preserved.")
            resource = self.verify(entry)
            if resource is None:
                continue
            if action == "clean":
                # kind's anonymous node volume belongs to this exact recorded container.
                args = ["container", "rm", "--force", "--volumes", entry["id"]]
            else:
                running = bool(resource["State"]["Running"])
                if running == (action == "resume"):
                    continue
                args = ["container", "stop" if action == "stop" else "start", entry["id"]]
            self.docker.require(self.docker.command(args, timeout=60, cancel=cancel))
        if action == "clean":
            self.docker.change("clean", cancel)
            self.lab.resources["kind_inventory"] = "[]"
            self.lab.resources.pop("kind_network", None)
            self.lab.resources.pop("cluster_ready", None)
            self.lab.resources.pop("kubeconfig_identity", None)
            self.lab.resources.pop("prepared_revision", None)
            self.save(self.lab)
            Path(self.env["KUBECONFIG"]).unlink(missing_ok=True)
        elif action == "resume":
            self.wait_ready(cancel)

    def fingerprint(self) -> str:
        records: list[Any] = []
        for entry in self.discover():
            node = self.verify(entry)
            if node:
                records.append([entry, node["State"]["Running"], node["State"]["StartedAt"]])
        kinds = (
            "deploy,sts,ds,pod,job,cronjob,svc,cm,secret,pvc,pv,storageclass,"
            "networkpolicy,sa,role,rolebinding,clusterrole,clusterrolebinding,ingress,"
            "node,namespace,hpa,pdb,resourcequota,limitrange,apiservice"
        )
        capabilities = json.loads(self.lab.resources.get("cluster_capabilities", "[]"))
        if "workerpool" in capabilities:
            kinds += ",customresourcedefinitions,workerpools.learning.dockyard.local"
        if "routing" in capabilities:
            kinds += ",gateways.gateway.networking.k8s.io,httproutes.gateway.networking.k8s.io"
        if "loadbalancer" in capabilities:
            kinds += ",ipaddresspools.metallb.io,l2advertisements.metallb.io"
        result = self.kubectl(
            [
                "get",
                kinds,
                "--all-namespaces",
                "-o",
                "json",
            ],
            output_limit=8_000_000,
        )
        if result.truncated:
            raise RuntimeErrorBase(
                "The cluster state exceeded the bounded observation size. "
                "Remove unneeded practice resources before checking again."
            )
        if result.ok:
            for item in json.loads(result.stdout)["items"]:
                metadata = item["metadata"]
                if metadata.get("namespace") in {
                    "kube-system",
                    "kube-public",
                    "kube-node-lease",
                    "local-path-storage",
                    "dockyard-observer",
                }:
                    continue
                records.append(
                    [
                        item["kind"],
                        metadata.get("namespace"),
                        metadata["name"],
                        metadata["uid"],
                        metadata.get("generation"),
                        metadata.get("labels"),
                        item.get("spec"),
                        item.get("data"),
                        item.get("rules"),
                        item.get("subjects"),
                        [
                            [container.get("containerID"), container.get("restartCount")]
                            for container in item.get("status", {}).get("containerStatuses", [])
                        ],
                    ]
                )
        else:
            records.append(["api-unavailable", result.returncode])
        return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
