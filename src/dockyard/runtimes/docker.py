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
                ) < datetime.fromisoformat(self.lab.created_at).replace(microsecond=0):
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
            raise RuntimeErrorBase("A recorded resource changed identity; it was preserved.")
        return resource

    def change(self, action: str, cancel: threading.Event) -> None:
        inventory = self.discover()
        inventory.sort(key=lambda item: ("container", "network", "volume").index(item["kind"]))
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
                args = [item["kind"], "rm"]
                if item["kind"] == "container":
                    args.append("--force")
                self.require(self.command([*args, item["id"]], timeout=45, cancel=cancel))
        if action == "clean":
            self.lab.resources["docker_inventory"] = "[]"
            self.lab.resources.pop("container_id", None)
            self.save(self.lab)

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
