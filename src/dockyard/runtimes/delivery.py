"""App-owned smart HTTP Git, registry, and Flux for actual local delivery practice."""

from __future__ import annotations

import json
import socket
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from dockyard.process import run
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.toolchain import Toolchain
from dockyard.workspace import atomic_write

if TYPE_CHECKING:
    from dockyard.runtimes.kubernetes import KubernetesRuntime

# The pinned Git image serves the repository itself, so nothing else is downloaded.
GIT_SERVER = (Path(__file__).parent / "git_http.pl").read_text()


def install(runtime: KubernetesRuntime, cancel: threading.Event) -> None:
    docker, env, lab = runtime.docker, runtime.env, runtime.lab

    def report(message: str) -> None:
        lab.resources["stage"] = message
        runtime.save(lab)

    flux = Toolchain(runtime.tools).ensure("flux", cancel, report)
    report("Starting the owned Git server and image registry")
    for purpose, port, selected_image, command in (
        ("git", 8080, env["DOCKYARD_GIT_IMAGE"], ["-e", GIT_SERVER]),
        ("registry", 5000, env["DOCKYARD_REGISTRY_IMAGE"], []),
    ):
        name = f"dockyard-{lab.id[:12]}-{purpose}"
        if docker.inspect("container", name) is not None:
            raise RuntimeErrorBase("The delivery service name is already occupied; preserved.")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            assigned_port = listener.getsockname()[1]
        options = ["--entrypoint", "perl"] if purpose == "git" else []
        if purpose == "registry":
            volume = name + "-data"
            if docker.inspect("volume", volume) is not None:
                raise RuntimeErrorBase("The delivery volume name is already occupied; preserved.")
            try:
                docker.require(
                    docker.command(
                        [
                            "volume",
                            "create",
                            "--label",
                            f"io.dockyard.lab={lab.id}",
                            volume,
                        ]
                    )
                )
            finally:
                docker.discover()
            options = [
                "--volume",
                volume + ":/var/lib/registry",
                "--env",
                "REGISTRY_LOG_LEVEL=error",
                "--env",
                "OTEL_TRACES_EXPORTER=none",
            ]
        try:
            result = docker.command(
                [
                    "run",
                    "-d",
                    "--name",
                    name,
                    "--label",
                    f"io.dockyard.lab={lab.id}",
                    "--network",
                    env["DOCKYARD_NETWORK"],
                    "--publish",
                    f"127.0.0.1:{assigned_port}:{port}",
                    "--memory",
                    "128m",
                    "--cpus",
                    "0.5",
                    *options,
                    selected_image,
                    *command,
                ],
                cancel=cancel,
            )
            docker.require(result)
        finally:
            docker.discover()
        instance = docker.inspect("container", result.stdout.strip())
        if instance is None:
            raise RuntimeErrorBase("The delivery service disappeared during preparation.")
        host_port = instance["NetworkSettings"]["Ports"][f"{port}/tcp"][0]["HostPort"]
        if purpose == "git":
            lab.resources["git_url"] = f"http://127.0.0.1:{host_port}/cgi-bin/git/dispatch.git"
            lab.resources["git_cluster_url"] = f"http://{name}:8080/cgi-bin/git/dispatch.git"
        else:
            registry = f"127.0.0.1:{host_port}"
            lab.resources["registry"] = registry
            # Match kind's documented per-registry mirror pattern, inside owned nodes only.
            config = f'[host."http://{name}:5000"]\n  capabilities = ["pull", "resolve"]\n'
            for node in runtime.discover():
                if runtime.verify(node) is None:
                    raise RuntimeErrorBase("A recorded node disappeared during registry setup.")
                directory = f"/etc/containerd/certs.d/{registry}"
                docker.require(docker.command(["exec", node["id"], "mkdir", "-p", directory]))
                path = runtime.root / "registry-hosts.toml"
                atomic_write(path, config.encode())
                docker.require(
                    docker.command(["cp", str(path), f"{node['id']}:{directory}/hosts.toml"])
                )
        runtime.save(lab)
    report("Installing and observing the pinned Flux controllers")
    exported = run(
        [str(flux), "install", "--components=source-controller,kustomize-controller", "--export"],
        env=env,
        timeout=60,
        cancel=cancel,
    )
    docker.require(exported)
    documents: list[dict[str, Any]] = list(yaml.safe_load_all(exported.stdout))
    for document in documents:
        if document["kind"] == "Deployment":
            name = document["metadata"]["name"]
            container = document["spec"]["template"]["spec"]["containers"][0]
            key = "flux_source" if name == "source-controller" else "flux_kustomize"
            container["image"] = env[f"DOCKYARD_{key.upper()}_LOCAL_IMAGE"]
            container["resources"] = {
                "requests": {"cpu": "50m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "512Mi"},
            }
            container["args"] = [
                "--watch-all-namespaces=false" if arg == "--watch-all-namespaces=true" else arg
                for arg in container["args"]
            ]
            document["spec"]["template"]["spec"].pop("priorityClassName", None)
    docker.require(
        runtime.kubectl(
            ["apply", "--server-side", "-f", "-"],
            payload=yaml.safe_dump_all(documents),
            timeout=120,
            cancel=cancel,
        )
    )
    for name in ("source-controller", "kustomize-controller"):
        docker.require(
            runtime.kubectl(
                ["rollout", "status", f"deploy/{name}", "-n", "flux-system", "--timeout=180s"],
                timeout=190,
                cancel=cancel,
            )
        )
    lab.resources["delivery_services"] = json.dumps(["git", "registry"])
    runtime.save(lab)
