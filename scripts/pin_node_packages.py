"""Pin the offline Kubernetes node packages for one version and architecture.

Usage: python scripts/pin_node_packages.py VERSION ARCH BASE_MANIFEST

The Kubernetes packages (kubeadm, kubelet, kubectl, cri-tools, kubernetes-cni) are
read from the signed pkgs.k8s.io repository for VERSION's minor release: the
repository key verifies InRelease, InRelease verifies the package index, and the
index verifies every downloaded package. The Ubuntu packages are copied from
BASE_MANIFEST, which must target the same guest image. The manifest is written
next to the others in src/dockyard/content/runtime/linux.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "src/dockyard/content/runtime/linux"
KUBERNETES_PACKAGES = ("kubeadm", "kubelet", "kubectl", "cri-tools", "kubernetes-cni")


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as response:
        return bytes(response.read())


def stanzas(index: str) -> list[dict[str, str]]:
    entries = []
    for block in index.strip().split("\n\n"):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            if line[:1] != " " and ":" in line:
                key, value = line.split(":", 1)
                fields[key] = value.strip()
        entries.append(fields)
    return entries


def verified_index(repository: str) -> str:
    """Return the package index after verifying its signature chain."""
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        (directory / "key.asc").write_bytes(fetch(repository + "Release.key"))
        subprocess.run(
            ["gpg", "--batch", "--quiet", "--dearmor", "--output", "keyring.gpg", "key.asc"],
            cwd=directory,
            check=True,
        )
        release = fetch(repository + "InRelease")
        (directory / "InRelease").write_bytes(release)
        subprocess.run(
            ["gpgv", "--keyring", "./keyring.gpg", "InRelease"],
            cwd=directory,
            check=True,
            capture_output=True,
        )
    index = fetch(repository + "Packages")
    expected = next(
        line.split()[0]
        for line in release.decode().split("SHA256:", 1)[1].splitlines()
        if line.strip().endswith(" Packages")
    )
    if hashlib.sha256(index).hexdigest() != expected:
        raise SystemExit("The package index does not match the signed release file.")
    return index.decode()


def version_key(version: str) -> list[int]:
    return [int(part) for part in version.split("-")[0].split(".")]


def main(version: str, architecture: str, base_manifest: Path) -> None:
    minor = ".".join(version.split(".")[:2])
    repository = f"https://pkgs.k8s.io/core:/stable:/v{minor}/deb/"
    entries = [
        entry
        for entry in stanzas(verified_index(repository))
        if entry.get("Architecture") in {architecture, "all"}
    ]
    base = json.loads(base_manifest.read_text())
    label = f"ubuntu24-kubernetes{version}"
    packages = {
        name: {**record, "version": label}
        for name, record in base["packages"].items()
        if not name.startswith(KUBERNETES_PACKAGES)
    }
    installed = {
        name: value
        for name, value in base["installed_versions"].items()
        if name not in KUBERNETES_PACKAGES
    }
    for package in KUBERNETES_PACKAGES:
        candidates = [entry for entry in entries if entry["Package"] == package]
        if package in {"kubeadm", "kubelet", "kubectl"}:
            candidates = [entry for entry in candidates if entry["Version"] == version + "-1.1"]
        if not candidates:
            raise SystemExit(f"No {package} package for {version} on {architecture}.")
        chosen = max(candidates, key=lambda entry: version_key(entry["Version"]))
        url = repository + chosen["Filename"]
        body = fetch(url)
        digest = hashlib.sha256(body).hexdigest()
        if digest != chosen["SHA256"] or len(body) != int(chosen["Size"]):
            raise SystemExit(f"{url} does not match its signed index entry.")
        filename = Path(chosen["Filename"]).name
        packages[filename] = {
            "path": "native/packages/" + filename,
            "sha256": digest,
            "size": len(body),
            "upstream_checksum": "SHA256:" + chosen["SHA256"],
            "url": url,
            "version": label,
        }
        installed[package] = chosen["Version"]
        print(f"{package} {chosen['Version']} {digest}")
    record = {
        "base_image_sha256": base["base_image_sha256"],
        "installed_versions": dict(sorted(installed.items())),
        "kubernetes": version,
        "packages": dict(sorted(packages.items())),
    }
    suffix = "-amd64" if architecture == "amd64" else ""
    output = DESTINATION / f"packages-{version}{suffix}.json"
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("wrote", output.relative_to(ROOT))


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[2] not in {"arm64", "amd64"}:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
