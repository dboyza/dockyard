"""Docker inventory with identity checks before every lifecycle mutation."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from datetime import datetime
from typing import Any

from dockyard.models import Lab
from dockyard.process import ProcessResult, run

LABEL = "io.dockyard.lab"


class RuntimeErrorBase(RuntimeError):
    pass


def ownership_start(lab: Lab) -> datetime:
    """When this lab began owning resources, on the Docker engine's own clock when recorded.

    Docker Desktop's VM clock pauses while the computer sleeps and can lag the host
    for minutes afterwards, so resource creation times are compared with a time read
    from the same engine. Labs recorded before that reading existed use host time.
    """
    return datetime.fromisoformat(
        (lab.resources.get("docker_clock") or lab.created_at).replace("Z", "+00:00")
    )


class DockerRuntime:
    def __init__(self, lab: Lab, env: dict[str, str], save: Callable[[Lab], None]):
        self.lab = lab
        self.env = env
        self.save = save

    def command(
        self, args: list[str], *, timeout: float = 30, cancel: threading.Event | None = None
    ) -> ProcessResult:
        return run(["docker", *args], env=self.env, timeout=timeout, cancel=cancel)

    @staticmethod
    def require(result: ProcessResult) -> None:
        if not result.ok:
            raise RuntimeErrorBase(result.stderr.strip() or "Docker operation did not complete.")

    def inspect(self, kind: str, identity: str) -> dict[str, Any] | None:
        result = self.command([kind, "inspect", identity])
        if not result.ok:
            if "no such" in result.stderr.lower() or "not found" in result.stderr.lower():
                return None
            self.require(result)
        return dict(json.loads(result.stdout)[0])

    @staticmethod
    def labels(kind: str, resource: dict[str, Any]) -> dict[str, str]:
        return dict(
            (resource.get("Config", {}) if kind == "container" else resource).get("Labels") or {}
        )

    @staticmethod
    def identity(kind: str, resource: dict[str, Any]) -> str:
        return str(resource["Name"] if kind == "volume" else resource["Id"])

    @staticmethod
    def created(resource: dict[str, Any]) -> str:
        return str(resource.get("Created") or resource.get("CreatedAt") or "")

    def discover(self) -> list[dict[str, str]]:
        """Adopt explicitly lab-labeled resources created after allocation, then persist IDs."""
        inventory = json.loads(self.lab.resources.get("docker_inventory", "[]"))
        known = {(item["kind"], item["id"], item["created"]) for item in inventory}
        for kind in ("container", "network", "volume"):
            args = [kind, "ls", "--quiet", "--filter", f"label={LABEL}={self.lab.id}"]
            if kind == "container":
                args.append("--all")
            result = self.command(args)
            self.require(result)
            for identity in result.stdout.split():
                resource = self.inspect(kind, identity)
                if resource is None:
                    continue
                if self.labels(kind, resource).get(LABEL) != self.lab.id:
                    raise RuntimeErrorBase(
                        "Resource ownership changed during discovery; preserved."
                    )
                created = self.created(resource)
                # Volumes may expose only whole seconds; compare at their available precision.
                if not created or datetime.fromisoformat(created.replace("Z", "+00:00")).replace(
                    microsecond=0
                ) < ownership_start(self.lab).replace(microsecond=0):
                    raise RuntimeErrorBase(
                        "A labeled resource predates this lab; it was preserved."
                    )
                item = {"kind": kind, "id": self.identity(kind, resource), "created": created}
                key = (kind, item["id"], created)
                if key not in known:
                    inventory.append(item)
                    known.add(key)
        self.lab.resources["docker_inventory"] = json.dumps(inventory)
        self.save(self.lab)
        return list(inventory)

    def verify(self, item: dict[str, str]) -> dict[str, Any] | None:
        resource = self.inspect(item["kind"], item["id"])
        if resource is None:
            return None
        if (
            self.identity(item["kind"], resource) != item["id"]
            or self.created(resource) != item["created"]
            or self.labels(item["kind"], resource).get(LABEL) != self.lab.id
        ):
            raise RuntimeErrorBase(
                "Something with this lab's name was changed outside Dockyard, "
                "so Dockyard left it untouched. "
                "Reset the lab to start again."
            )
        return resource

    def change(self, action: str, cancel: threading.Event) -> None:
        inventory = self.discover()
        inventory.sort(key=lambda item: ("container", "network", "volume").index(item["kind"]))
        ports: set[str] = set()
        for item in inventory:
            if cancel.is_set():
                raise RuntimeErrorBase("Operation canceled. Remaining resources are preserved.")
            resource = self.verify(item)
            if resource is None:
                continue
            if action in {"stop", "resume"}:
                if item["kind"] != "container":
                    continue
                running = resource["State"]["Running"]
                if (action == "stop" and not running) or (action == "resume" and running):
                    continue
                verb = "stop" if action == "stop" else "start"
                self.require(
                    self.command(["container", verb, item["id"]], timeout=45, cancel=cancel)
                )
            elif action == "clean":
                for bindings in (resource.get("NetworkSettings", {}).get("Ports") or {}).values():
                    ports.update(binding["HostPort"] for binding in bindings or [])
                args = [item["kind"], "rm"]
                if item["kind"] == "container":
                    # Anonymous volumes belong to this exact recorded container; named ones
                    # are separate inventory items and are never removed by this flag.
                    args += ["--force", "--volumes"]
                self.require(self.command([*args, item["id"]], timeout=45, cancel=cancel))
        if action == "clean":
            self.lab.resources["docker_inventory"] = "[]"
            self.lab.resources.pop("container_id", None)
            self.save(self.lab)
            self.remove_images(ports, cancel)

    def remove_images(self, ports: set[str], cancel: threading.Event) -> None:
        """Untag images named for this lab or held in its own loopback registries.

        Images still used by a container are preserved, and nothing is forced.
        """
        listed = self.command(
            ["image", "ls", "--digests", "--format", "{{json .}}"], timeout=60, cancel=cancel
        )
        if not listed.ok:
            return  # Only VM labs reach this without Docker, and they may have built nothing.
        recorded = (
            self.lab.resources.get("registry_port", ""),
            self.lab.resources.get("registry", "").rpartition(":")[2],
        )
        hosts = {
            f"{address}:{port}"
            for port in ports.union(recorded) - {""}
            for address in ("127.0.0.1", "localhost")
        }
        for line in listed.stdout.splitlines():
            image = json.loads(line)
            repository, tag, digest = image["Repository"], image["Tag"], image["Digest"]
            owned = repository.partition("/")[0] in hosts
            if not owned and repository != f"dockyard-{self.lab.id[:12]}":
                continue
            if tag != "<none>":
                reference = f"{repository}:{tag}"
            elif digest != "<none>":
                reference = f"{repository}@{digest}"
            else:
                continue
            if cancel.is_set():
                raise RuntimeErrorBase("Operation canceled. Remaining images are preserved.")
            result = self.command(["image", "rm", reference], timeout=60, cancel=cancel)
            message = result.stderr.lower()
            if not result.ok and "conflict" not in message and "no such image" not in message:
                self.require(result)

    def fingerprint(self) -> str:
        """Stable identity/running/restart observations, excluding constantly changing counters."""
        records = []
        for item in self.discover():
            resource = self.verify(item)
            if resource is None:
                continue
            state = resource.get("State", {})
            records.append(
                [item, state.get("Running"), state.get("StartedAt"), resource.get("RestartCount")]
            )
        return json.dumps(records, sort_keys=True)
