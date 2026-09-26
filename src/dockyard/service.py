"""Shared learner operations used by the browser and real-terminal CLI."""

from __future__ import annotations

import json
import os
import re
import secrets
import shlex
import shutil
import socket
import sys
import threading
import uuid
from pathlib import Path
from typing import Any

from dockyard.catalog import CONTENT, Catalog
from dockyard.locking import operation_lock
from dockyard.models import (
    Assessment,
    CheckStatus,
    Criterion,
    Evidence,
    Lab,
    LabObservation,
    Runtime,
)
from dockyard.portfolio import checkpoint
from dockyard.process import ProcessResult, run
from dockyard.runtimes.docker import DockerRuntime, RuntimeErrorBase
from dockyard.runtimes.kubernetes import KubernetesRuntime
from dockyard.store import Store, timestamp
from dockyard.workspace import atomic_write, reset, snapshot, write_files

COMPATIBILITY = json.loads((CONTENT / "compatibility.json").read_text())
PYTHON_IMAGE: str = COMPATIBILITY["images"]["python"]


class LabError(RuntimeErrorBase):
    pass


class Service:
    def __init__(self, directory: Path, catalog: Catalog | None = None):
        self.directory = directory.resolve()
        self.store = Store(self.directory)
        self.catalog = catalog or Catalog()
        development_tools = Path(__file__).resolve().parents[2] / ".tools"
        self.tools = development_tools if development_tools.exists() else self.directory / "tools"
        self._cancels: dict[str, threading.Event] = {}
        self._lock = threading.Lock()
        self.closing = threading.Event()

    def shutdown(self) -> None:
        self.closing.set()
        with self._lock:
            for cancel in self._cancels.values():
                cancel.set()

    @staticmethod
    def public_lab(lab: Lab) -> dict[str, Any]:
        body = lab.model_dump(mode="json")
        body["resources"] = {
            key: value
            for key, value in lab.resources.items()
            if key not in {"db_password", "bootstrap_token"}
        }
        return body

    @staticmethod
    def redact(value: str, lab: Lab) -> str:
        for key in ("db_password", "bootstrap_token"):
            secret = lab.resources.get(key)
            if secret:
                value = value.replace(secret, "[redacted lab credential]")
        return value

    def environment(self, lab: Lab | None = None) -> dict[str, str]:
        env = dict(os.environ)
        for key in list(env):
            if key.startswith(("HELM_", "GIT_")):
                env.pop(key)
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_TERMINAL_PROMPT="0")
        env.pop("DOCKER_CONTEXT", None)
        env.pop("WEZTERM_UNIX_SOCKET", None)
        env.pop("KIND_EXPERIMENTAL_DOCKER_NETWORK", None)
        env["KIND_EXPERIMENTAL_PROVIDER"] = "docker"
        env["PATH"] = (
            f"{self.tools / 'bin'}:{Path(sys.executable).parent}:{env.get('PATH', '/usr/bin:/bin')}"
        )
        for name, image in COMPATIBILITY["images"].items():
            env[f"DOCKYARD_{name.upper()}_IMAGE"] = image
            env[f"DOCKYARD_{name.upper()}_LOCAL_IMAGE"] = (
                f"dockyard-cache/{name.replace('_', '-')}:{image.split('sha256:')[-1][:16]}"
            )
        if lab:
            env.update(
                DOCKYARD_LAB=lab.id,
                DOCKYARD_UNIT=lab.unit_id,
                DOCKYARD_CONTAINER=f"dockyard-{lab.id[:12]}",
                DOCKYARD_WORKSPACE=lab.workspace,
                DOCKYARD_PORT=lab.resources["port"],
                DOCKYARD_PYTHON_IMAGE=PYTHON_IMAGE,
                KUBECONFIG=str(Path(lab.workspace).parent / "kubeconfig"),
                DOCKER_HOST=lab.resources["docker_endpoint"],
                DOCKYARD_DATA=str(self.directory),
                COMPOSE_PROJECT_NAME=f"dockyard-{lab.id[:12]}",
                DOCKYARD_PROJECT=f"dockyard-{lab.id[:12]}",
                DOCKYARD_NETWORK=f"dockyard-{lab.id[:12]}-net",
                DOCKYARD_VOLUME=f"dockyard-{lab.id[:12]}-data",
                DOCKYARD_IMAGE=f"dockyard-{lab.id[:12]}:practice",
                DOCKYARD_STORAGE=str(Path(lab.workspace).parent / "data"),
                DOCKYARD_DB_PASSWORD=lab.resources.get("db_password", "practice-only"),
                DOCKYARD_REGISTRY_PORT=lab.resources.get("registry_port", ""),
                DOCKYARD_CLUSTER=f"dockyard-{lab.id[:12]}",
                DOCKYARD_NAMESPACE="dispatch",
                DOCKYARD_TLS_PORT=lab.resources.get("registry_port", ""),
                DOCKYARD_TLS_CERT=str(Path(lab.workspace).parent / "data/tls.crt"),
                HELM_CACHE_HOME=str(Path(lab.workspace).parent / "helm/cache"),
                HELM_CONFIG_HOME=str(Path(lab.workspace).parent / "helm/config"),
                HELM_DATA_HOME=str(Path(lab.workspace).parent / "helm/data"),
                HELM_PLUGINS=str(Path(lab.workspace).parent / "helm/plugins"),
                HELM_DRIVER="secret",
                HELM_NAMESPACE="dispatch",
            )
            for key in ("git_url", "git_cluster_url", "registry"):
                if lab.resources.get(key):
                    env["DOCKYARD_" + key.upper()] = lab.resources[key]
            if lab.resources.get("kind_network"):
                env["KIND_EXPERIMENTAL_DOCKER_NETWORK"] = lab.resources["kind_network"]
        return env

    def doctor(self) -> dict[str, Any]:
        env = self.environment()
        tools = {
            name: shutil.which(name, path=env["PATH"])
            for name in ("docker", "kubectl", "kind", "wezterm")
        }
        docker = (
            run([tools["docker"], "info", "--format", "{{.ServerVersion}}"], timeout=10)
            if tools["docker"]
            else None
        )
        return {
            "tools": tools,
            "docker_ready": bool(docker and docker.ok),
            "docker_version": docker.stdout.strip() if docker and docker.ok else None,
            "docker_error": docker.stderr.strip() if docker and not docker.ok else None,
            "free_disk_gib": round(shutil.disk_usage(self.directory).free / 1024**3, 1),
        }

    def _docker_endpoint(self) -> str:
        endpoint = os.environ.get("DOCKER_HOST")
        if not endpoint:
            result = run(["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"])
            if not result.ok:
                raise LabError("Docker is unavailable. Start Docker Desktop and run doctor again.")
            endpoint = result.stdout.strip()
        if not endpoint.startswith("unix://"):
            raise LabError("Dockyard requires a local Unix-socket Docker endpoint.")
        return endpoint

    def _allocate_lab(self, unit_id: str) -> Lab:
        existing = self.store.lab(unit_id)
        if existing:
            return existing
        unit = self.catalog.get(unit_id)
        lab_id = uuid.uuid4().hex
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
            with socket.socket() as registry_listener:
                registry_listener.bind(("127.0.0.1", 0))
                registry_port = registry_listener.getsockname()[1]
        lab = Lab(
            id=lab_id,
            unit_id=unit_id,
            revision=unit.revision,
            runtime=unit.runtime,
            state="absent",
            workspace=str(self.directory / "labs" / lab_id / "workspace"),
            created_at=timestamp(),
            updated_at=timestamp(),
            resources={
                "port": str(port),
                "docker_endpoint": self._docker_endpoint(),
                "db_password": secrets.token_urlsafe(24),
                "registry_port": str(registry_port),
            },
        )
        self.store.save_lab(lab)
        return lab

    def _save(self, lab: Lab) -> None:
        lab.updated_at = timestamp()
        self.store.save_lab(lab)

    def perform(self, unit_id: str, action: str) -> dict[str, Any]:
        self.catalog.get(unit_id)
        with operation_lock(self.directory / "locks", unit_id):
            existing = self.store.lab(unit_id)
            if existing:
                self.store.recover_operations(existing.id)
            return self._perform(unit_id, action)

    def _perform(self, unit_id: str, action: str) -> dict[str, Any]:
        if action not in {"prepare", "check", "reset", "retake", "stop", "resume", "clean"}:
            raise ValueError("Unknown lab operation.")
        self.catalog.get(unit_id)
        lab = self._allocate_lab(unit_id)
        operation_id = self.store.begin_operation(lab.id, action)
        cancel = threading.Event()
        with self._lock:
            self._cancels[operation_id] = cancel
        try:
            result: dict[str, Any]
            if action == "prepare":
                self._prepare(lab, cancel)
                result = self.public_lab(lab)
            elif action == "check":
                result = self._check(lab, cancel).model_dump(mode="json")
            elif action in {"reset", "retake"}:
                self._cleanup(lab, cancel)
                backup = reset(
                    Path(lab.workspace),
                    self.catalog.get(unit_id).starter,
                    self.directory / "backups",
                )
                lab.resources.pop("container_id", None)
                lab.resources.pop("prepared_revision", None)
                self._prepare(lab, cancel)
                if action == "retake":
                    self.store.start_attempt(unit_id, self.catalog.get(unit_id).revision)
                result = {"backup": str(backup), "lab": self.public_lab(lab)}
            elif action == "clean":
                self._cleanup(lab, cancel)
                lab.resources.pop("prepared_revision", None)
                lab.state = "absent"
                self._save(lab)
                result = self.public_lab(lab)
            else:
                if action == "stop":
                    lab.state = "stopping"
                    self._save(lab)
                self.runtime(lab).change(action, cancel)
                lab.state = "stopped" if action == "stop" else "ready"
                self._save(lab)
                result = self.public_lab(lab)
            if cancel.is_set():
                raise LabError("The operation was canceled. Your workspace has been preserved.")
            self.store.update_operation(operation_id, "done")
            return result
        except Exception as error:
            lab.state = "failed"
            lab.error = self.redact(str(error), lab)
            self._save(lab)
            self.store.update_operation(
                operation_id, "canceled" if cancel.is_set() else "failed", lab.error
            )
            raise LabError(lab.error) from error
        finally:
            with self._lock:
                self._cancels.pop(operation_id, None)

    def cancel(self, operation_id: str) -> None:
        with self._lock:
            event = self._cancels.get(operation_id)
            if event:
                event.set()
                self.store.update_operation(operation_id, "canceling")

    @staticmethod
    def _require(result: ProcessResult) -> None:
        if not result.ok:
            if result.canceled:
                raise LabError("Operation canceled.")
            if result.timed_out:
                raise LabError(
                    "The operation exceeded its deadline. Inspect lab status before retrying."
                )
            raise LabError(
                result.stderr.strip() or result.stdout.strip() or "The tool exited unsuccessfully."
            )

    def _prepare(self, lab: Lab, cancel: threading.Event) -> None:
        lab.state = "preparing"
        lab.error = None
        self._save(lab)
        unit = self.catalog.get(lab.unit_id)
        if unit.runtime == Runtime.LINUX:
            raise LabError("This runtime adapter is not available in this development build.")
        env = self.environment(lab)
        self._require(
            run(["docker", "info", "--format", "{{.ID}}"], env=env, timeout=15, cancel=cancel)
        )
        images = list(
            dict.fromkeys(unit.images + (["kind"] if unit.runtime == Runtime.KUBERNETES else []))
        )
        for image_name in images:
            image_ref = COMPATIBILITY["images"][image_name]
            image = run(
                ["docker", "image", "inspect", image_ref], env=env, timeout=15, cancel=cancel
            )
            if not image.ok:
                self._require(
                    run(["docker", "pull", image_ref], env=env, timeout=600, cancel=cancel)
                )
        workspace = Path(lab.workspace)
        if not workspace.exists():
            write_files(workspace, unit.starter)
        runtime = self.runtime(lab)
        if isinstance(runtime, KubernetesRuntime):
            with operation_lock(self.directory / "locks", "cluster-capacity"):
                for other in self.store.labs():
                    if (
                        other.id != lab.id
                        and other.runtime == Runtime.KUBERNETES
                        and other.state == "ready"
                    ):
                        with operation_lock(self.directory / "locks", other.unit_id):
                            self.runtime(other).change("stop", cancel)
                            other.state = "stopped"
                            self._save(other)
                runtime.prepare(unit.nodes, unit.images, cancel, unit.capabilities)
        env = self.environment(lab)
        commands = (
            [] if lab.resources.get("prepared_revision") == str(unit.revision) else unit.prepare
        )
        if commands and unit.runtime == Runtime.DOCKER:
            self.docker(lab).change("clean", cancel)
        for command in commands:
            outcome = run(
                [self.expand(arg, lab) for arg in command.args],
                env=env,
                cwd=workspace,
                timeout=command.timeout,
                cancel=cancel,
                input_text=self.expand(command.stdin, lab) if command.stdin else None,
            )
            self._require(outcome)
        runtime.discover()
        lab.resources["prepared_revision"] = str(unit.revision)
        lab.revision = unit.revision
        lab.state = "ready"
        self._save(lab)

    def expand(self, value: str, lab: Lab) -> str:
        values = {
            "lab_id": lab.id,
            "container": f"dockyard-{lab.id[:12]}",
            "port": lab.resources["port"],
            "workspace": lab.workspace,
            "python_image": PYTHON_IMAGE,
            "image": f"dockyard-{lab.id[:12]}:practice",
            "network": f"dockyard-{lab.id[:12]}-net",
            "volume": f"dockyard-{lab.id[:12]}-data",
            "project": f"dockyard-{lab.id[:12]}",
            "storage": str(Path(lab.workspace).parent / "data"),
            "registry_port": lab.resources.get("registry_port", ""),
            "cluster": f"dockyard-{lab.id[:12]}",
            "namespace": "dispatch",
        }
        values.update({f"{name}_image": image for name, image in COMPATIBILITY["images"].items()})
        for key, replacement in values.items():
            value = value.replace("{{" + key + "}}", replacement)
        return value

    def docker(self, lab: Lab) -> DockerRuntime:
        return DockerRuntime(lab, self.environment(lab), self._save)

    def runtime(self, lab: Lab) -> DockerRuntime | KubernetesRuntime:
        if lab.runtime == Runtime.KUBERNETES:
            return KubernetesRuntime(lab, self.environment(lab), self._save, self.tools)
        return self.docker(lab)

    def _cleanup(self, lab: Lab, cancel: threading.Event) -> None:
        lab.state = "cleaning"
        self._save(lab)
        self.runtime(lab).change("clean", cancel)

    def _check(self, lab: Lab, cancel: threading.Event) -> Assessment:
        unit = self.catalog.get(lab.unit_id)
        started = timestamp()
        workspace = Path(lab.workspace)
        if not workspace.exists():
            raise LabError("Prepare this lab before checking your work.")
        stopped = lab.state == "stopped"
        lab.state = "checking"
        self._save(lab)
        digest, _ = snapshot(workspace)
        env = self.environment(lab)
        runtime = self.runtime(lab)
        evidence: list[Evidence] = []
        runtime_before = None
        health = (
            None
            if stopped
            else run(["docker", "info", "--format", "{{.ID}}"], env=env, timeout=10, cancel=cancel)
        )
        if health is not None and health.ok and isinstance(runtime, KubernetesRuntime):
            health = runtime.health(cancel)
        if stopped:
            evidence.append(
                Evidence(
                    criterion="environment",
                    title="The lab is resumed",
                    status=CheckStatus.BLOCKED,
                    expected="An active practice environment",
                    observed="This lab was stopped through Dockyard.",
                    diagnostic=(
                        "Resume the lab, then check again. Pausing is not a learner mistake."
                    ),
                )
            )
        elif health is not None and not health.ok:
            evidence.append(
                Evidence(
                    criterion="environment",
                    title="The practice runtime is available",
                    status=CheckStatus.BLOCKED,
                    expected="A responsive local runtime and, where required, Kubernetes API",
                    observed=health.stderr,
                    diagnostic=(
                        "Check Docker Desktop and resume the practice environment, then retry. "
                        "This does not count as a learner mistake."
                    ),
                )
            )
        else:
            runtime_before = runtime.fingerprint()
            observations: dict[str, ProcessResult] = {}
            for criterion in unit.checks:
                evidence.append(self._criterion(criterion, lab, cancel, observations))
            if all(item.status == CheckStatus.PASS for item in evidence):
                runtime.discover()
        current_digest, _ = snapshot(workspace)
        if cancel.is_set():
            raise LabError("The check was canceled; no assessment was recorded.")
        status = CheckStatus.PASS
        if any(item.status == CheckStatus.BLOCKED for item in evidence):
            status = CheckStatus.BLOCKED
        elif any(item.status == CheckStatus.FAIL for item in evidence):
            status = CheckStatus.FAIL
        if current_digest != digest or (
            runtime_before is not None and runtime.fingerprint() != runtime_before
        ):
            status = CheckStatus.STALE
        progress = self.store.progress().get(unit.id, {})
        assessment = Assessment(
            id=uuid.uuid4().hex,
            unit_id=unit.id,
            revision=unit.revision,
            lab_id=lab.id,
            status=status,
            started_at=started,
            finished_at=timestamp(),
            file_digest=digest,
            evidence=evidence,
            independent=unit.kind != "lesson"
            and not (progress.get("hints") or progress.get("reference")),
            hints_used=int(progress.get("hints", 0)),
            reference_revealed=bool(progress.get("reference", False)),
            attempt=self.store.setting(f"attempt-number:{unit.id}", 1),
        )
        saved_checkpoint = None
        if assessment.status == CheckStatus.PASS and unit.kind == "mission":
            try:
                saved_checkpoint = checkpoint(
                    self.directory, lab, unit, assessment, self.store.note(unit.id)
                )
            except ValueError:
                assessment.status = CheckStatus.STALE
        self.store.save_assessment(assessment, saved_checkpoint)
        lab.state = "stopped" if stopped else "ready"
        self._save(lab)
        return assessment

    def _criterion(
        self,
        criterion: Criterion,
        lab: Lab,
        cancel: threading.Event,
        observations: dict[str, ProcessResult],
    ) -> Evidence:
        command = criterion.command
        try:
            key = command.model_dump_json()
            result = observations.get(key)
            if result is None:
                result = run(
                    [self.expand(arg, lab) for arg in command.args],
                    env=self.environment(lab),
                    cwd=Path(lab.workspace),
                    timeout=command.timeout,
                    cancel=cancel,
                    input_text=self.expand(command.stdin, lab) if command.stdin else None,
                )
                observations[key] = result
        except FileNotFoundError as error:
            return Evidence(
                criterion=criterion.id,
                title=criterion.title,
                status=CheckStatus.BLOCKED,
                expected=self.expand(criterion.expected, lab),
                observed=str(error),
                diagnostic="Run dockyard doctor to restore the missing tool.",
                points=criterion.points,
            )
        expected = self.expand(criterion.expected, lab)
        observed = (
            result.stderr
            if criterion.output == "stderr"
            else result.stdout + result.stderr
            if criterion.output == "combined"
            else result.stdout
        ).strip()
        matches = False
        details = ""
        if result.returncode in command.allowed_exit_codes and not (
            result.canceled or result.timed_out
        ):
            try:
                if criterion.expectation == "json":
                    value: Any = json.loads(observed)
                    if isinstance(value, dict) and criterion.json_path:
                        measurements = value.get("_details", {})
                        measured = (
                            measurements.get(str(criterion.json_path[0]))
                            if isinstance(measurements, dict)
                            else None
                        )
                        if measured is not None:
                            details = json.dumps(measured, indent=2, sort_keys=True)
                    for part in criterion.json_path:
                        value = value[int(part)] if isinstance(value, list) else value[str(part)]
                    observed = (
                        value if isinstance(value, str) else json.dumps(value, sort_keys=True)
                    )
                    matches = observed == expected
                elif criterion.expectation == "equals":
                    matches = observed == expected
                elif criterion.expectation == "matches":
                    matches = re.search(expected, observed) is not None
                elif criterion.expectation == "absent":
                    matches = expected not in observed
                else:
                    matches = expected in observed
            except (ValueError, KeyError, IndexError, TypeError):
                matches = False
        if result.stderr and criterion.output == "stdout":
            observed += "\n" + result.stderr.strip()
        return Evidence(
            criterion=criterion.id,
            title=criterion.title,
            status=(
                CheckStatus.BLOCKED
                if result.timed_out or result.canceled
                else CheckStatus.PASS
                if matches
                else CheckStatus.FAIL
            ),
            expected=expected,
            observed=self.redact(observed, lab)[-8000:],
            diagnostic=criterion.diagnostic,
            details=self.redact(details, lab)[-8000:],
            points=criterion.points,
        )

    def observe(self, unit_id: str) -> LabObservation:
        from dockyard.observations import observe

        unit = self.catalog.get(unit_id)
        lab = self.store.lab(unit_id)
        unavailable = LabObservation(
            lab_id=lab.id if lab else "",
            runtime=unit.runtime,
            observed_at=timestamp(),
            status="unavailable",
            message="Prepare and start this lab to observe its resources.",
        )
        if not lab or lab.state != "ready":
            if lab and lab.state == "stopped":
                unavailable.message = "The lab is paused. Resume it to observe current resources."
            elif lab and lab.state not in {"absent", "failed"}:
                unavailable.message = (
                    f"The lab is {lab.state}. Observation resumes when its operation finishes."
                )
            return unavailable
        try:
            observed = observe(self.runtime(lab))
            current = self.store.lab(unit_id)
            if not current or current.id != lab.id or current.state != "ready":
                unavailable.message = (
                    "The lab changed during observation. Refresh after its operation finishes."
                )
                return unavailable
            return observed
        except (RuntimeErrorBase, OSError, ValueError, KeyError, TypeError) as error:
            unavailable.message = self.redact(str(error), lab)[:1000]
            return unavailable

    def shell_command(self, unit_id: str) -> list[str]:
        lab = self.store.lab(unit_id)
        if lab is None or not Path(lab.workspace).exists():
            raise LabError("Prepare the lab before opening its terminal.")
        command = [
            sys.executable,
            "-m",
            "dockyard",
            "--data-dir",
            str(self.directory),
            "lab",
            "shell",
            unit_id,
        ]
        return command

    def open_terminal(self, unit_id: str) -> dict[str, str]:
        lab = self.store.lab(unit_id)
        if not lab:
            raise LabError("Prepare this lab first.")
        command = self.shell_command(unit_id)
        env = self.environment(lab)
        tab = run(
            ["wezterm", "cli", "--no-auto-start", "spawn", "--cwd", lab.workspace, "--", *command],
            env=env,
            timeout=8,
        )
        if not tab.ok:
            # GUI start is a deliberately long-lived process; the CLI child owns its lab shell.
            import subprocess

            subprocess.Popen(
                [
                    "wezterm",
                    "start",
                    "--always-new-process",
                    "--cwd",
                    lab.workspace,
                    "--",
                    *command,
                ],
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        return {"command": shlex.join(command), "workspace": lab.workspace}

    def write_shell_rc(self, lab: Lab) -> Path:
        directory = Path(lab.workspace).parent / "shell"
        directory.mkdir(parents=True, exist_ok=True)
        rc = (
            "# Dockyard lab shell; global dotfiles are not modified.\n"
            'autoload -Uz compinit && compinit -d "$ZDOTDIR/.zcompdump"\n'
            f"PROMPT='%F{{blue}}dockyard%f {lab.unit_id} "
            f"%F{{cyan}}{lab.id[:8]}%f %1~ %# '\n"
            "print 'Docker and Kubernetes commands here use this lab environment.'\n"
            "print 'Run dockyard lab check to inspect your work; exit closes this shell.'\n"
        )
        atomic_write(directory / ".zshrc", rc.encode())
        return directory
