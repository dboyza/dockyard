"""Record how much each pinned image and tool downloads, so lessons can say so before Prepare.

Image sizes are the compressed layers a registry sends, per architecture. Sizes are keyed
by the pinned reference or checksum, so a changed pin has no size until this runs again.

Usage: .venv/bin/python scripts/measure_downloads.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

CONTENT = Path(__file__).resolve().parents[1] / "src/dockyard/content"
ARCHITECTURES = ("arm64", "amd64")


def raw(reference: str) -> dict:
    result = subprocess.run(
        ["docker", "buildx", "imagetools", "inspect", "--raw", reference],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    return json.loads(result.stdout)


def repository(reference: str) -> str:
    name = reference.partition("@")[0]
    return name.rpartition(":")[0] if ":" in name.rpartition("/")[2] else name


def measure(reference: str) -> dict[str, int]:
    index = raw(reference)
    sizes = {}
    for architecture in ARCHITECTURES:
        entry = next(
            item
            for item in index["manifests"]
            if item["platform"]["os"] == "linux"
            and item["platform"]["architecture"] == architecture
        )
        manifest = raw(f"{repository(reference)}@{entry['digest']}")
        sizes[architecture] = manifest["config"]["size"] + sum(
            layer["size"] for layer in manifest["layers"]
        )
    return sizes


def pinned_files(node: Any) -> dict[str, str]:
    """Every pinned download in a manifest that does not record its own size."""
    found = {}
    if isinstance(node, dict):
        if "url" in node and "sha256" in node and "size" not in node:
            found[node["sha256"]] = node["url"]
        for value in node.values():
            found.update(pinned_files(value))
    elif isinstance(node, list):
        for value in node:
            found.update(pinned_files(value))
    return found


def content_length(url: str) -> int:
    try:
        with urlopen(Request(url, method="HEAD"), timeout=60) as response:
            return int(response.headers["Content-Length"])
    except (HTTPError, TypeError):
        # Some hosts answer only GET; ask for one byte and read the full length.
        with urlopen(Request(url, headers={"Range": "bytes=0-0"}), timeout=60) as response:
            return int(response.headers["Content-Range"].rpartition("/")[2])


def main() -> None:
    target = CONTENT / "download-sizes.json"
    known = json.loads(target.read_text()) if target.exists() else {"images": {}, "files": {}}
    images = {}
    for name, reference in json.loads((CONTENT / "compatibility.json").read_text())[
        "images"
    ].items():
        images[reference] = known["images"].get(reference) or measure(reference)
        print(f"{name}: {images[reference]['arm64'] // 1024**2} MiB")
    files = {}
    manifests = [
        *sorted(CONTENT.glob("toolchain*.json")),
        CONTENT / "runtime/linux/guest-tools.json",
    ]
    for manifest in manifests:
        for checksum, url in pinned_files(json.loads(manifest.read_text())).items():
            files[checksum] = known["files"].get(checksum) or content_length(url)
            print(f"{url.rpartition('/')[2]}: {files[checksum] // 1024**2} MiB")
    target.write_text(json.dumps({"images": images, "files": files}, indent=2) + "\n")


if __name__ == "__main__":
    main()
