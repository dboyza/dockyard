"""Pinned downloads: prefetch, offline readiness, and cleanup of what no lab still needs."""

from __future__ import annotations

import json
import os
import shutil
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dockyard.images import (
    ALIAS_PREFIX,
    PINNED,
    ImageStore,
    cluster_images,
    digest_reference,
    host_images,
    label,
)
from dockyard.locking import operation_lock
from dockyard.models import Runtime, Unit
from dockyard.process import run
from dockyard.runtimes.node_packages import manifest as package_manifest
from dockyard.runtimes.scanner import ready as scanner_ready
from dockyard.service import LabError
from dockyard.store import BusyError
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
    raise ValueError("Choose a unit, module:0 through module:30, track:0 through track:5, or all.")


def dependencies(unit: Unit) -> dict[str, Any]:
    capabilities = set(unit.capabilities)
    tools = capabilities & MANIFEST.keys()
    packages: dict[str, Any] = {}
    limitations = []
    if unit.runtime == Runtime.KUBERNETES:
        tools |= {"kind", "kubectl", "calico"}
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
    if "routing" in capabilities:
        tools |= {"gateway", "traefik-rbac"}
    if "loadbalancer" in capabilities:
        tools.add("metallb")
    if "metrics" in capabilities:
        tools.add("metrics-server")
    if "delivery" in capabilities:
        tools.add("flux")
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
        # Images Docker holds on this computer, then images kept as private archives.
        "host_images": host_images(unit),
        "cluster_images": cluster_images(unit),
        "packages": packages,
        "scanner": "scanner" in capabilities,
        "limitations": limitations,
    }


def docker_environment(service: Service) -> dict[str, str]:
    env = service.environment()
    env["DOCKER_HOST"] = service._docker_endpoint()
    return env


def directory_size(root: Path) -> int:
    size = 0
    if root.is_dir():
        for directory, folders, files in os.walk(root, followlinks=False):
            folders[:] = [name for name in folders if not (Path(directory) / name).is_symlink()]
            for name in files:
                path = Path(directory) / name
                if not path.is_symlink():
                    size += path.stat().st_size
    return size


def inventory(service: Service, scope: str) -> dict[str, Any]:
    units = select(service, scope)
    requirements = {unit.id: dependencies(unit) for unit in units}
    tool_names = sorted({name for dep in requirements.values() for name in dep["tools"]})
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
    store = ImageStore(service.tools, env)
    host_names = sorted({name for dep in requirements.values() for name in dep["host_images"]})
    cluster_names = sorted(
        {name for dep in requirements.values() for name in dep["cluster_images"]}
    )
    images = [
        {
            "name": name,
            "reference": PINNED[name],
            "kept": "docker",
            "ready": engine.ok and store.on_host(name),
        }
        for name in host_names
    ] + [
        {"name": name, "reference": PINNED[name], "kept": "private", "ready": store.archived(name)}
        for name in cluster_names
    ]
    scanner = (
        scanner_ready(service.tools / "trivy")
        if any(dep["scanner"] for dep in requirements.values())
        else None
    )
    missing_tools = {entry["name"] for entry in installed if not entry["ready"]}
    missing_host = {e["name"] for e in images if e["kept"] == "docker" and not e["ready"]}
    missing_cluster = {e["name"] for e in images if e["kept"] == "private" and not e["ready"]}
    missing_packages = {entry["name"] for entry in installed_packages if not entry["ready"]}
    readiness = []
    for unit in units:
        dep = requirements[unit.id]
        missing = sorted(
            (set(dep["tools"]) & missing_tools)
            | (set(dep["host_images"]) & missing_host)
            | (set(dep["cluster_images"]) & missing_cluster)
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
    size = directory_size(service.tools)
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
        "Images only clusters use are private archives, so they stay out of your Docker image "
        "list. Dockyard never prunes Docker globally.",
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
            # A prefetched scope stays downloaded until the learner frees the space.
            kept = service.store.setting("kept-scopes", [])
            if scope not in kept:
                service.store.set_setting("kept-scopes", [*kept, scope])
            env = docker_environment(service)
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
            store = ImageStore(service.tools, env)
            host_names = sorted({name for dep in requirements for name in dep["host_images"]})
            for name in host_names:
                report(f"Checking the {label(name)} image")
                store.ensure_host(name, cancel, report)
            service.store.set_setting(
                "host-images",
                sorted(
                    set(service.store.setting("host-images", []))
                    | {digest_reference(PINNED[name]) for name in host_names}
                ),
            )
            for name in sorted({name for dep in requirements for name in dep["cluster_images"]}):
                report(f"Checking the {label(name)} image")
                store.ensure_archive(name, cancel, report)
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
    """Image references in Docker that Dockyard itself created.

    These are pinned digest pulls, digests this profile recorded before a pin changed,
    and cache aliases from earlier versions, whose tags record a digest prefix.
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
        if row["Repository"].startswith(ALIAS_PREFIX) and row["Tag"] != "<none>"
    )
    prefixes = {alias.rpartition(":")[2] for alias in aliases}
    known = {digest_reference(reference) for reference in PINNED.values()} | set(
        service.store.setting("host-images", [])
    )
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
        if reference in known or reference.partition("@sha256:")[2][:16] in prefixes
    }
    return aliases + sorted(digests)


def needed(service: Service) -> tuple[set[str], set[str]]:
    """Pinned images to keep, as names: those Docker holds, then private archives.

    Existing labs need theirs, the module being studied keeps its next lesson ready,
    and a scope the learner prefetched stays until they free the space.
    """
    catalog = service.catalog
    units = {
        lab.unit_id
        for lab in service.store.labs()
        if lab.state != "absent" and lab.unit_id in catalog.units
    }
    current = catalog.units.get(service.store.setting("last_unit") or "")
    if current and current.kind in {"lesson", "mission"}:
        units |= {
            unit.id
            for unit in catalog.units.values()
            if unit.module == current.module and unit.kind in {"lesson", "mission"}
        }
    for scope in service.store.setting("kept-scopes", []):
        try:
            units |= {unit.id for unit in select(service, scope)}
        except (ValueError, KeyError):
            continue
    selected = [catalog.units[unit_id] for unit_id in units]
    return (
        {name for unit in selected for name in host_images(unit)},
        {name for unit in selected for name in cluster_images(unit)},
    )


def remove(service: Service, keep_host: set[str], keep_cluster: set[str]) -> dict[str, Any]:
    """Remove Dockyard's downloaded images except the named ones; images in use stay."""
    with operation_lock(service.directory / "locks", "cache-prefetch"):
        env = docker_environment(service)
        store = ImageStore(service.tools, env)
        keep = {digest_reference(PINNED[name]) for name in keep_host}
        removed, kept, freed = [], [], 0
        for reference in pulled_references(service):
            if reference in keep:
                continue
            result = run(["docker", "image", "rm", reference], env=env, timeout=60)
            message = result.stderr.lower()
            if result.ok or "no such image" in message:
                removed.append(reference)
            elif "conflict" in message or "in use" in message or "being used" in message:
                kept.append(reference)
            else:
                service._require(result)
        archives = {store.archive_path(name) for name in keep_cluster}
        if store.directory.is_dir() and not store.directory.is_symlink():
            for path in sorted(store.directory.iterdir()):
                if path not in archives and path.is_file() and not path.is_symlink():
                    freed += path.stat().st_size
                    path.unlink()
                    removed.append(path.name)
        service.store.set_setting(
            "host-images",
            sorted(set(service.store.setting("host-images", [])) & (keep | set(kept))),
        )
        return {"removed": removed, "kept_in_use": kept, "freed_archive_bytes": freed}


def clean(service: Service) -> dict[str, Any]:
    """Remove every image Dockyard downloaded, and forget prefetched scopes."""
    service.store.set_setting("kept-scopes", [])
    return remove(service, set(), set())


def sweep(service: Service) -> dict[str, Any] | None:
    """Remove downloads nothing needs any more, unless the learner chose to keep them.

    Never raises: tidying up must not fail the lab operation that triggered it.
    """
    # Profiles that share tools must not decide for each other what stays downloaded.
    if service.shared_tools or service.store.setting("keep-downloads", False):
        return None
    try:
        return remove(service, *needed(service))
    except (BusyError, LabError, OSError, ValueError):
        return None


def storage(service: Service) -> dict[str, Any]:
    """What Dockyard has downloaded and where it is kept, for the learner to review."""
    env = docker_environment(service)
    store = ImageStore(service.tools, env)
    engine = run(["docker", "info", "--format", "{{.ID}}"], env=env, timeout=10)
    keep_host, keep_cluster = needed(service)
    references = pulled_references(service) if engine.ok else []
    names = {digest_reference(reference): name for name, reference in PINNED.items()}
    present = [reference for reference in references if not reference.startswith(ALIAS_PREFIX)]
    sizes = (
        run(
            ["docker", "image", "inspect", "--format", "{{.Size}}", *present],
            env=env,
            timeout=30,
        )
        if present
        else None
    )
    measured = sizes.stdout.split() if sizes and sizes.ok else []
    host_images = [
        {
            "name": names.get(reference, reference),
            # A digest this profile pulled before an update changed the pin.
            "label": label(names[reference]) if reference in names else "Earlier pinned image",
            "bytes": int(size) if size.isdigit() else 0,
            "needed": names.get(reference) in keep_host,
        }
        for reference, size in zip(present, measured, strict=False)
    ]
    archive_sizes = {
        name: store.archive_path(name).stat().st_size for name in PINNED if store.archived(name)
    }
    archives = [
        {"name": name, "label": label(name), "bytes": size, "needed": name in keep_cluster}
        for name, size in archive_sizes.items()
    ]
    legacy = [reference for reference in references if reference.startswith(ALIAS_PREFIX)]
    return {
        "docker_ready": engine.ok,
        "host_images": host_images,
        "archives": archives,
        "legacy_aliases": len(legacy),
        "tools_bytes": directory_size(service.tools) - sum(archive_sizes.values()),
        "keep_downloads": bool(service.store.setting("keep-downloads", False)),
        "kept_scopes": service.store.setting("kept-scopes", []),
        "free_disk_gib": round(shutil.disk_usage(service.directory).free / 1024**3, 1),
    }
