"""Versioned dependency prefetch and explicit offline readiness, without global pruning."""

from __future__ import annotations

import json
import os
import shutil
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dockyard import host
from dockyard.locking import operation_lock
from dockyard.models import Runtime, Unit
from dockyard.process import run
from dockyard.runtimes import calico
from dockyard.runtimes.node_packages import manifest as package_manifest
from dockyard.runtimes.scanner import ready as scanner_ready
from dockyard.service import COMPATIBILITY, LabError
from dockyard.toolchain import MANIFEST, Toolchain
from dockyard.versions import KUBERNETES, native

if TYPE_CHECKING:
    from dockyard.service import Service


def select(service: Service, scope: str) -> list[Unit]:
    ordered = sorted(service.catalog.units.values(), key=lambda unit: (unit.module, unit.order))
    if scope == "all":
        return ordered
    kind, _, value = scope.partition(":")
    if kind == "unit":
        return [service.catalog.get(value)]
    if kind in {"module", "track"} and value.isdigit():
        number = int(value)
        modules = {
            m["id"]
            for m in service.catalog.modules
            if kind == "module" and m["id"] == number or kind == "track" and m["phase"] == number
        }
        units = [u for u in ordered if u.module in modules]
        if units:
            return units
    raise ValueError("Choose a unit, module:0 through module:24, track:0 through track:4, or all.")


def dependencies(unit: Unit) -> dict[str, Any]:
    capabilities = set(unit.capabilities)
    tools = capabilities & MANIFEST.keys()
    images = set(unit.images)
    packages: dict[str, Any] = {}
    limitations = []
    if "python-image" in capabilities:
        images.add("python")
    for name in ("postgres", "redis"):
        if name + "-image" in capabilities:
            images.add(name)
    if unit.runtime == Runtime.KUBERNETES:
        tools |= {"kind", "kubectl", "calico"}
        images |= {"kind", *calico.upstream_images()}
    if unit.runtime == Runtime.LINUX:
        tools |= {"limactl", "lima-guestagent", "ubuntu-node", "kubectl"}
        versions = {native(unit.native_version)}
        if unit.native_version == "previous":
            # Upgrade lessons also stage the version they upgrade to.
            versions.add(KUBERNETES)
        for version in versions:
            packages.update(package_manifest(version)["packages"])
        if unit.node_tools:
            from dockyard.runtimes.guest_tools import archive_entries

            packages.update(archive_entries(list(unit.node_tools)))
        if capabilities & {"native-cluster", "native-control-plane"}:
            limitations.append(
                "Fresh kubeadm bootstrap and upgrades still require registry access "
                "for control-plane images. Prepared native labs remain locally usable."
            )
    if "native-csi" in capabilities:
        from dockyard.runtimes.native_csi import CONTAINERS

        images.update(CONTAINERS.values())
    if "routing" in capabilities:
        tools |= {"gateway", "traefik-rbac"}
    if "loadbalancer" in capabilities:
        tools.add("metallb")
    if "metrics" in capabilities:
        tools.add("metrics-server")
    if "delivery" in capabilities:
        tools |= {"flux", "git-daemon", "busybox-extras"}
    if "scanner" in capabilities:
        tools |= {"trivy", "pyjwt-fixture"}
    if any(
        "pip download" in text or "pip install" in text
        for text in [*unit.starter.values(), *unit.reference.values()]
    ):
        limitations.append(
            "Dependency image builds can need the Python package index after Docker "
            "build-cache eviction. Cached base images alone do not prove offline builds."
        )
    return {
        "tools": sorted(tools),
        "images": sorted(images),
        "packages": packages,
        "scanner": "scanner" in capabilities,
        "limitations": limitations,
    }


def inventory(service: Service, scope: str) -> dict[str, Any]:
    units = select(service, scope)
    requirements = {unit.id: dependencies(unit) for unit in units}
    tool_names = sorted({name for dep in requirements.values() for name in dep["tools"]})
    image_names = sorted({name for dep in requirements.values() for name in dep["images"]})
    packages = {
        name: entry for dep in requirements.values() for name, entry in dep["packages"].items()
    }
    tools = Toolchain(service.tools)
    installed = [
        {"name": name, "version": MANIFEST[name]["version"], "ready": tools.ready(name)}
        for name in tool_names
    ]
    package_tools = Toolchain(service.tools, packages)
    installed_packages = [
        {"name": name, "ready": package_tools.ready(name)} for name in sorted(packages)
    ]
    env = service.environment()
    env["DOCKER_HOST"] = service._docker_endpoint()
    engine = run(["docker", "info", "--format", "{{.ID}}"], env=env, timeout=10)
    images = []
    for name in image_names:
        reference = COMPATIBILITY["images"][name]
        result = (
            run(
                [
                    "docker",
                    "image",
                    "inspect",
                    "--platform=linux/" + host.architecture(),
                    "--format",
                    "{{.Architecture}}",
                    reference,
                ],
                env=env,
                timeout=10,
            )
            if engine.ok
            else None
        )
        images.append(
            {
                "name": name,
                "reference": reference,
                "ready": bool(
                    result and result.ok and result.stdout.strip() == host.architecture()
                ),
            }
        )
    scanner = (
        scanner_ready(service.tools / "trivy")
        if any(dep["scanner"] for dep in requirements.values())
        else None
    )
    missing_tools = {entry["name"] for entry in installed if not entry["ready"]}
    missing_images = {entry["name"] for entry in images if not entry["ready"]}
    missing_packages = {entry["name"] for entry in installed_packages if not entry["ready"]}
    readiness = []
    for unit in units:
        dep = requirements[unit.id]
        missing = sorted(
            (set(dep["tools"]) & missing_tools)
            | (set(dep["images"]) & missing_images)
            | (dep["packages"].keys() & missing_packages)
        )
        if dep["scanner"] and not scanner:
            missing.append("pinned vulnerability database")
        readiness.append(
            {
                "unit_id": unit.id,
                "title": unit.title,
                "missing": missing,
                "limitations": dep["limitations"],
                "status": "missing"
                if missing
                else "network-required"
                if dep["limitations"]
                else "cached",
            }
        )
    size = 0
    if service.tools.is_dir():
        for directory, folders, files in os.walk(service.tools, followlinks=False):
            folders[:] = [name for name in folders if not (Path(directory) / name).is_symlink()]
            for name in files:
                path = Path(directory) / name
                if not path.is_symlink():
                    size += path.stat().st_size
    return {
        "scope": scope,
        "units": readiness,
        "tools": installed,
        "images": images,
        "packages": installed_packages,
        "scanner_ready": scanner,
        "docker_ready": engine.ok,
        "private_cache_gib": round(size / 1024**3, 2),
        "soft_budget_gib": 40,
        "over_soft_budget": size > 40 * 1024**3,
        "free_disk_gib": round(shutil.disk_usage(service.directory).free / 1024**3, 1),
        "policy": "Cached means the declared runtime tools, packages, and image digests "
        "are present. Network-required identifies remaining external build or bootstrap steps. "
        "Docker images and build cache are shared with Docker Desktop; "
        "Dockyard never prunes them globally.",
    }


def prepare(
    service: Service, scope: str, notify: Callable[[str], None] | None = None
) -> dict[str, Any]:
    units = select(service, scope)
    with operation_lock(service.directory / "locks", "cache-prefetch"):
        service.store.recover_operations("cache")
        identity = service.store.begin_operation("cache", "prefetch " + scope)
        cancel = threading.Event()
        with service._lock:
            service._cancels[identity] = cancel

        def report(message: str) -> None:
            if cancel.is_set():
                raise LabError("Cache preparation canceled; verified downloads are preserved.")
            service.store.update_operation(identity, "running", message)
            if notify:
                notify(message)

        try:
            if shutil.disk_usage(service.directory).free < 5 * 1024**3:
                raise LabError("Free at least 5 GiB before prefetching dependencies.")
            env = service.environment()
            env["DOCKER_HOST"] = service._docker_endpoint()
            requirements = [dependencies(unit) for unit in units]
            tools = Toolchain(service.tools)
            for name in sorted({name for dep in requirements for name in dep["tools"]}):
                tools.ensure(name, cancel, report)
            packages = {
                name: entry for dep in requirements for name, entry in dep["packages"].items()
            }
            installer = Toolchain(service.tools, packages)
            for name in sorted(packages):
                installer.ensure(name, cancel, report)
            for name in sorted({name for dep in requirements for name in dep["images"]}):
                reference = COMPATIBILITY["images"][name]
                report("Checking pinned native-architecture image: " + name)
                found = run(
                    [
                        "docker",
                        "image",
                        "inspect",
                        "--platform=linux/" + host.architecture(),
                        "--format",
                        "{{.Architecture}}",
                        reference,
                    ],
                    env=env,
                    timeout=10,
                )
                if not found.ok or found.stdout.strip() != host.architecture():
                    report("Downloading pinned native-architecture image: " + name)
                    result = run(
                        ["docker", "pull", "--platform=linux/" + host.architecture(), reference],
                        env=env,
                        timeout=900,
                        cancel=cancel,
                    )
                    service._require(result)
            if any(dep["scanner"] for dep in requirements):
                from dockyard.runtimes.scanner import ensure_database

                ensure_database(service.tools, env, cancel, report)
            report("Verifying selected dependency cache")
            verified = inventory(service, scope)
            service.store.update_operation(
                identity, "done", "Dependency cache verified for " + scope
            )
            return verified
        except Exception as error:
            service.store.update_operation(
                identity, "canceled" if cancel.is_set() else "failed", str(error)
            )
            raise
        finally:
            with service._lock:
                service._cancels.pop(identity, None)


def pulled_references(service: Service) -> list[str]:
    """Image references Dockyard itself created: cache aliases and pinned digest pulls.

    Superseded pins are recognized through their alias, which records the digest prefix.
    Tags that people add themselves are never included, even on the same image.
    """
    env = docker_environment(service)
    listed = run(
        ["docker", "image", "ls", "--digests", "--format", "{{json .}}"], env=env, timeout=30
    )
    service._require(listed)
    rows = [json.loads(line) for line in listed.stdout.splitlines()]
    aliases = sorted(
        f"{row['Repository']}:{row['Tag']}"
        for row in rows
        if row["Repository"].startswith("dockyard-cache/") and row["Tag"] != "<none>"
    )
    prefixes = {alias.rpartition(":")[2] for alias in aliases}
    pinned = set()
    for reference in COMPATIBILITY["images"].values():
        name, _, digest = reference.partition("@")
        if ":" in name.rpartition("/")[2]:
            name = name.rpartition(":")[0]
        pinned.add(f"{name}@{digest}")
    candidates = {
        f"{row['Repository']}@{row['Digest']}"
        for row in rows
        if row["Tag"] == "<none>" and row["Digest"].startswith("sha256:")
    }
    if aliases:
        # Docker may list a digest pull only as part of the alias's image, not as its own row.
        inspected = run(
            ["docker", "image", "inspect", "--format", "{{json .RepoDigests}}", *aliases],
            env=env,
            timeout=30,
        )
        service._require(inspected)
        for line in inspected.stdout.splitlines():
            candidates.update(json.loads(line) or [])
    digests = {
        reference
        for reference in candidates
        if reference in pinned or reference.partition("@sha256:")[2][:16] in prefixes
    }
    return aliases + sorted(digests)


def docker_environment(service: Service) -> dict[str, str]:
    env = service.environment()
    env["DOCKER_HOST"] = service._docker_endpoint()
    return env


def clean(service: Service) -> dict[str, Any]:
    """Remove Dockyard's downloaded images without forcing; images in use stay."""
    with operation_lock(service.directory / "locks", "cache-prefetch"):
        env = docker_environment(service)
        removed, kept = [], []
        for reference in pulled_references(service):
            result = run(["docker", "image", "rm", reference], env=env, timeout=60)
            message = result.stderr.lower()
            if result.ok or "no such image" in message:
                removed.append(reference)
            elif "conflict" in message or "in use" in message or "being used" in message:
                kept.append(reference)
            else:
                service._require(result)
        return {"removed": removed, "kept_in_use": kept}
