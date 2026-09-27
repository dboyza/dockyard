"""A private authenticated registry with a real Kubernetes pull-identity failure."""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from dockyard.fixtures.incident import prepare
from dockyard.models import Runtime
from dockyard.probes.kubernetes import kubectl, owned_pods
from dockyard.process import run
from dockyard.runtimes.kubernetes import KubernetesRuntime
from dockyard.service import Service
from dockyard.workspace import atomic_write


def secret(registry: str, password: str) -> dict[str, object]:
    config = {
        "auths": {registry: {"auth": base64.b64encode(("learner:" + password).encode()).decode()}}
    }
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": "registry-pull", "namespace": "dispatch"},
        "type": "kubernetes.io/dockerconfigjson",
        "stringData": {".dockerconfigjson": json.dumps(config)},
    }


def install(*, broken: bool = True) -> None:
    service = Service(Path(os.environ["DOCKYARD_DATA"]))
    lab = service.store.lab(os.environ["DOCKYARD_UNIT"])
    if (
        lab is None
        or lab.id != os.environ["DOCKYARD_LAB"]
        or lab.runtime != Runtime.KUBERNETES
        or Path(lab.workspace).resolve() != Path.cwd().resolve()
    ):
        raise RuntimeError("This shell no longer identifies the current Kubernetes incident.")
    r = KubernetesRuntime(lab, service.environment(lab), service.store.save_lab, service.tools)
    # Record the intact application before introducing its pull failure.
    prepare("registry")
    auth = r.root / "data/registry-auth"
    auth.mkdir(mode=0o700, parents=True, exist_ok=True)
    hashed = run(
        ["/usr/sbin/htpasswd", "-niB", "learner"], input_text=lab.resources["db_password"] + "\n"
    )
    r.docker.require(hashed)
    atomic_write(auth / "htpasswd", hashed.stdout.encode())
    name = "dockyard-" + lab.id[:12] + "-private-registry"
    volume = name + "-data"
    for kind, value in (("container", name), ("volume", volume)):
        if r.docker.inspect(kind, value) is not None:
            raise RuntimeError("An incident registry resource name is occupied; preserved.")
    try:
        r.docker.require(
            r.docker.command(["volume", "create", "--label", "io.dockyard.lab=" + lab.id, volume])
        )
        created = r.docker.command(
            [
                "run",
                "-d",
                "--name",
                name,
                "--label",
                "io.dockyard.lab=" + lab.id,
                "--network",
                os.environ["DOCKYARD_NETWORK"],
                "--publish",
                "127.0.0.1::5000",
                "--memory",
                "128m",
                "--cpus",
                "0.5",
                "--volume",
                volume + ":/var/lib/registry",
                "--volume",
                str(auth) + ":/auth:ro",
                "--env",
                "REGISTRY_AUTH=htpasswd",
                "--env",
                "REGISTRY_AUTH_HTPASSWD_REALM=Dockyard",
                "--env",
                "REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd",
                "--env",
                "REGISTRY_LOG_LEVEL=error",
                "--env",
                "OTEL_TRACES_EXPORTER=none",
                os.environ["DOCKYARD_REGISTRY_IMAGE"],
            ]
        )
        r.docker.require(created)
    finally:
        r.docker.discover()
    container = r.docker.inspect("container", created.stdout.strip())
    assert container is not None
    registry = "127.0.0.1:" + container["NetworkSettings"]["Ports"]["5000/tcp"][0]["HostPort"]
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            with urlopen("http://" + registry + "/v2/", timeout=2):
                raise RuntimeError("The practice registry unexpectedly allowed anonymous access.")
        except HTTPError as error:
            if error.code == 401:
                error.close()
                break
            raise
        except OSError:
            time.sleep(0.5)
    else:
        raise RuntimeError("The authenticated registry did not become reachable.")
    atomic_write(Path(lab.workspace) / "registry.txt", (registry + "\n").encode())
    from dockyard.runtimes.registry_publish import publish

    archive = r.root / "data/publish-image.tar"
    r.docker.require(
        r.docker.command(["save", "-o", str(archive), os.environ["DOCKYARD_IMAGE"]], timeout=120)
    )
    try:
        digest = publish(archive, registry, lab.resources["db_password"])
        atomic_write(
            r.root / "data/registry-release.json",
            json.dumps({"registry": registry, "digest": digest}).encode(),
        )
    finally:
        archive.unlink(missing_ok=True)
    image = registry + "/dispatch:incident"
    hosts = r.root / "incident-registry-hosts.toml"
    atomic_write(
        hosts, (f'[host."http://{name}:5000"]\n  capabilities = ["pull", "resolve"]\n').encode()
    )
    for node in r.discover():
        if r.verify(node) is None:
            raise RuntimeError("A recorded owned node disappeared during registry configuration.")
        directory = "/etc/containerd/certs.d/" + registry
        r.docker.require(r.docker.command(["exec", node["id"], "mkdir", "-p", directory]))
        r.docker.require(
            r.docker.command(["cp", str(hosts), node["id"] + ":" + directory + "/hosts.toml"])
        )
    r.docker.require(
        r.kubectl(
            ["apply", "-f", "-"],
            payload=json.dumps(
                secret(
                    registry,
                    "expired-practice-credential" if broken else lab.resources["db_password"],
                )
            ),
        )
    )
    patch = {
        "spec": {
            "strategy": {"type": "Recreate", "rollingUpdate": None},
            "template": {
                "spec": {
                    "imagePullSecrets": [{"name": "registry-pull"}],
                    "containers": [{"name": "api", "image": image, "imagePullPolicy": "Always"}],
                }
            },
        }
    }
    kubectl("patch", "deployment", "dispatch", "--type=strategic", "-p", json.dumps(patch))
    if not broken:
        kubectl("rollout", "status", "deployment/dispatch", "--timeout=120s", timeout=130)
        return
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        _, pods = owned_pods("dispatch")
        if len(pods) == 2 and all(
            any(
                s.get("state", {}).get("waiting", {}).get("reason")
                in {"ErrImagePull", "ImagePullBackOff"}
                for s in p.get("status", {}).get("containerStatuses", [])
            )
            for p in pods
        ):
            break
        time.sleep(1)
    else:
        raise RuntimeError("The incident did not produce a real registry pull failure.")
    print("The private registry is reachable; the workload pull identity fails authentication.")


if __name__ == "__main__":
    install()
