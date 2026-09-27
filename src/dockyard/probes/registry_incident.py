"""Require real authenticated image resolution and a fresh private-image execution."""

from __future__ import annotations

import base64
import json
import os
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dockyard.probes.incident import observe
from dockyard.probes.kubernetes import get, kubectl, owned_pods
from dockyard.process import run


def registry() -> dict[str, Any]:
    result = observe("registry")
    result["contract"] = False
    name = "registry-proof-" + uuid.uuid4().hex[:10]
    try:
        host = Path("registry.txt").read_text().strip()
        original = json.loads(
            (
                Path(os.environ["DOCKYARD_DATA"])
                / "labs"
                / os.environ["DOCKYARD_LAB"]
                / "data/registry-release.json"
            ).read_text()
        )
        if original["registry"] != host:
            return result
        expected = "127.0.0.1:"
        if not host.startswith(expected) or not host[len(expected) :].isdigit():
            return result
        unauthorized = False
        try:
            with urlopen("http://" + host + "/v2/", timeout=3):
                pass
        except HTTPError as error:
            unauthorized = error.code == 401
            error.close()
        authorization = base64.b64encode(
            ("learner:" + os.environ["DOCKYARD_REGISTRY_PASSWORD"]).encode()
        ).decode()
        request = Request(
            "http://" + host + "/v2/dispatch/manifests/incident",
            headers={
                "Authorization": "Basic " + authorization,
                "Accept": "application/vnd.oci.image.index.v1+json,"
                "application/vnd.oci.image.manifest.v1+json,"
                "application/vnd.docker.distribution.manifest.v2+json",
            },
        )
        with urlopen(request, timeout=3) as response:
            digest = response.headers["Docker-Content-Digest"]
            config_digest = json.loads(response.read(1_000_000))["config"]["digest"]
        if digest != original["digest"]:
            return result
        _, pods = owned_pods("dispatch")
        if len(pods) != 2:
            return result
        api = next(c for c in pods[0]["spec"]["containers"] if c["name"] == "api")
        image = api["image"]
        if image not in (host + "/dispatch:incident", host + "/dispatch@" + digest):
            return result
        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": name, "namespace": "dispatch"},
            "spec": {
                "restartPolicy": "Never",
                "terminationGracePeriodSeconds": 0,
                "imagePullSecrets": pods[0]["spec"].get("imagePullSecrets", []),
                "containers": [
                    {
                        "name": "proof",
                        "image": image,
                        "imagePullPolicy": "Always",
                        "command": [
                            "python",
                            "-c",
                            "from pathlib import Path; "
                            "print(Path('/app/VERSION').read_text().strip())",
                        ],
                    }
                ],
            },
        }
        created = run(["kubectl", "create", "-f", "-"], input_text=json.dumps(manifest))
        if not created.ok:
            return result
        kubectl(
            "wait",
            "pod/" + name,
            "--for=jsonpath={.status.phase}=Succeeded",
            "--timeout=45s",
            timeout=50,
        )
        proof = get("pod", name)
        result["contract"] = (
            unauthorized
            and kubectl("logs", name) == Path("VERSION").read_text().strip()
            and any(
                str(proof["status"]["containerStatuses"][0].get("imageID", "")).endswith(identity)
                for identity in (digest, config_digest)
            )
            and all(
                c.get("imagePullPolicy") == "Always"
                for p in pods
                for c in p["spec"]["containers"]
                if c["name"] == "api"
            )
        )
    except (OSError, RuntimeError, ValueError, KeyError, StopIteration):
        pass
    finally:
        with suppress(RuntimeError):
            kubectl(
                "delete",
                "pod",
                name,
                "--ignore-not-found",
                "--wait=true",
                "--timeout=20s",
                timeout=25,
            )
    return result


if __name__ == "__main__":
    print(json.dumps(registry()))
