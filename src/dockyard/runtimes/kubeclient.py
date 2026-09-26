"""A local Kubernetes API client with an explicit inline-credential boundary."""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from urllib.parse import urlparse

import yaml

from dockyard.process import ProcessResult, run
from dockyard.runtimes.docker import RuntimeErrorBase


def identity(path: Path) -> str:
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


def command(
    args: list[str],
    *,
    tools: Path,
    env: dict[str, str],
    expected: str | None,
    timeout: float = 30,
    cancel: threading.Event | None = None,
    payload: str | None = None,
    output_limit: int = 1_000_000,
) -> ProcessResult:
    if not expected or identity(Path(env["KUBECONFIG"])) != expected:
        raise RuntimeErrorBase("The kubeconfig no longer matches this recorded lab cluster.")
    return run(
        [
            str(tools / "bin/kubectl"),
            "--kubeconfig",
            env["KUBECONFIG"],
            "--request-timeout=15s",
            *args,
        ],
        env=env,
        timeout=timeout,
        cancel=cancel,
        input_text=payload,
        output_limit=output_limit,
    )
