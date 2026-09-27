"""Publish a verified local native-architecture OCI image through an owned loopback registry API."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import tarfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from dockyard import host


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        raise ValueError("The local registry unexpectedly redirected an authenticated request.")


def publish(archive: Path, registry: str, password: str) -> str:
    if not re.fullmatch(r"127\.0\.0\.1:[0-9]{1,5}", registry):
        raise ValueError("Practice image publishing requires the recorded loopback registry.")
    origin = "http://" + registry
    opener = build_opener(NoRedirect())
    authorization = "Basic " + base64.b64encode(("learner:" + password).encode()).decode()

    def request(
        path: str, method: str, body: bytes | None = None, media: str = "application/octet-stream"
    ) -> Any:
        url = urljoin(origin, path)
        if urlsplit(url).scheme != "http" or urlsplit(url).netloc != registry:
            raise ValueError("The registry upload location left the recorded loopback endpoint.")
        return opener.open(
            Request(
                url,
                data=body,
                method=method,
                headers={"Authorization": authorization, "Content-Type": media},
            ),
            timeout=30,
        )

    with tarfile.open(archive) as saved:

        def read(name: str, limit: int) -> bytes:
            member = saved.getmember(name)
            if not member.isreg() or member.size > limit:
                raise ValueError("The owned OCI archive contains an invalid or oversized member.")
            stream = saved.extractfile(member)
            if stream is None:
                raise ValueError("An expected OCI member was unavailable.")
            with stream:
                return stream.read(limit + 1)

        def blob(descriptor: dict[str, Any]) -> bytes:
            digest = str(descriptor["digest"])
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
                raise ValueError("The owned image contains an unsupported content identity.")
            data = read("blobs/sha256/" + digest.split(":")[1], 256 * 1024**2)
            if (
                len(data) != descriptor["size"]
                or "sha256:" + hashlib.sha256(data).hexdigest() != digest
            ):
                raise ValueError("The owned OCI image did not match its declared content identity.")
            return data

        def image(
            descriptors: list[dict[str, Any]], depth: int = 0
        ) -> tuple[bytes, dict[str, Any]]:
            if depth > 5:
                raise ValueError("The owned OCI index is unexpectedly nested.")
            for descriptor in descriptors:
                platform = descriptor.get("platform", {})
                if platform and (
                    platform.get("architecture") != host.architecture()
                    or platform.get("os") != "linux"
                ):
                    continue
                data = blob(descriptor)
                document = json.loads(data)
                if "manifests" in document:
                    return image(document["manifests"], depth + 1)
                if "config" in document:
                    config = json.loads(blob(document["config"]))
                    if (
                        config.get("architecture") == host.architecture()
                        and config.get("os") == "linux"
                    ):
                        return data, document
            raise ValueError("No Linux native-architecture image was found in the owned archive.")

        manifest_bytes, manifest = image(json.loads(read("index.json", 1_000_000))["manifests"])
        for descriptor in [manifest["config"], *manifest["layers"]]:
            data = blob(descriptor)
            digest = descriptor["digest"]
            try:
                with request("/v2/dispatch/blobs/" + digest, "HEAD"):
                    continue
            except HTTPError as error:
                missing = error.code == 404
                error.close()
                if not missing:
                    raise
            with request("/v2/dispatch/blobs/uploads/", "POST", b"") as response:
                location = response.headers["Location"]
            location += ("&" if "?" in location else "?") + urlencode({"digest": digest})
            with request(location, "PUT", data) as response:
                if response.status != 201:
                    raise ValueError("The registry did not acknowledge its uploaded image content.")
        with request(
            "/v2/dispatch/manifests/incident", "PUT", manifest_bytes, manifest["mediaType"]
        ) as response:
            digest = str(response.headers["Docker-Content-Digest"])
        if digest != "sha256:" + hashlib.sha256(manifest_bytes).hexdigest():
            raise ValueError("The registry returned a different image manifest identity.")
        return digest
