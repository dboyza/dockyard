"""App-owned Lima guests with recorded filesystem identities and no host mounts."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from dockyard.catalog import CONTENT
from dockyard.models import Lab
from dockyard.process import ProcessResult, run
from dockyard.runtimes import kubeclient
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.toolchain import MANIFEST, Toolchain, digest
from dockyard.workspace import atomic_write


class LinuxRuntime:
    def __init__(self, lab: Lab, env: dict[str, str], save: Callable[[Lab], None], tools: Path):
        self.lab, self.save, self.tools = lab, save, tools
        self.root = Path(lab.workspace).parent
        self.home = self.root.parent.parent / "vms"
        self.env = {k: v for k, v in env.items() if not k.startswith("LIMA_")}
        self.env.update(
            LIMA_HOME=str(self.home),
            SSH="/usr/bin/ssh",
            KUBECONFIG=str(self.root / "kubeconfig"),
        )
        self.executable = tools / "bin/limactl"

    def report(self, message: str) -> None:
        self.lab.resources["stage"] = message
        self.save(self.lab)

    def command(
        self,
        args: list[str],
        *,
        timeout: float = 30,
        cancel: threading.Event | None = None,
        input_text: str | None = None,
    ) -> ProcessResult:
        return run(
            [str(self.executable), "--tty=false", *args],
            env=self.env,
            timeout=timeout,
            cancel=cancel,
            input_text=input_text,
        )

    @staticmethod
    def require(result: ProcessResult) -> None:
        if not result.ok:
            raise RuntimeErrorBase(result.stderr.strip() or "The Linux guest operation failed.")

    def listing(self) -> dict[str, dict[str, Any]]:
        if not self.home.exists():
            return {}
        result = self.command(["list", "--json"])
        self.require(result)
        return {
            item["name"]: item
            for line in result.stdout.splitlines()
            if line.strip()
            for item in [json.loads(line)]
        }

    def identity(self, name: str) -> dict[str, str]:
        directory = self.home / name
        if directory.is_symlink() or not directory.resolve().is_relative_to(self.home.resolve()):
            raise RuntimeErrorBase("The VM directory boundary changed; preserved.")
        configuration, disk = directory / "lima.yaml", directory / "disk"
        if configuration.is_symlink() or disk.is_symlink():
            raise RuntimeErrorBase("A VM identity file is a symbolic link; preserved.")
        value = yaml.safe_load(configuration.read_text())
        if value.get("mounts") or value.get("vmType") != "vz" or value.get("arch") != "aarch64":
            raise RuntimeErrorBase(
                "The VM no longer has the approved no-mount ARM64 configuration."
            )
        stat = disk.stat()
        return {
            "name": name,
            "directory": str(directory.resolve()),
            "configuration": digest(configuration),
            "disk_device": str(stat.st_dev),
            "disk_inode": str(stat.st_ino),
            "disk_created": str(stat.st_birthtime),
        }

    def discover(self) -> list[dict[str, str]]:
        # Adoption is limited to a create intent written before limactl was invoked.
        inventory: list[dict[str, str]] = json.loads(self.lab.resources.get("vm_inventory", "[]"))
        existing = self.listing()
        names = {entry["name"] for entry in inventory}
        for name in json.loads(self.lab.resources.get("vm_intent", "[]")):
            if name in names or name not in existing:
                continue
            entry = self.identity(name)
            if existing[name]["dir"] != str(self.home / name):
                raise RuntimeErrorBase("The VM provider returned an unexpected directory.")
            intent = json.loads((self.root / "vm-intent.json").read_text())
            if intent.get("lab") != self.lab.id or name not in intent.get("names", []):
                raise RuntimeErrorBase("The VM creation record does not match this lab.")
            directory = self.home / name
            if directory.stat().st_birthtime < intent["created"]:
                raise RuntimeErrorBase("The VM predates its creation intent; preserved.")
            inventory.append(entry)
            names.add(name)
        self.lab.resources["vm_inventory"] = json.dumps(inventory)
        self.save(self.lab)
        return inventory

    def verify(self, entry: dict[str, str]) -> dict[str, Any] | None:
        existing = self.listing().get(entry["name"])
        if existing is None:
            return None
        if self.identity(entry["name"]) != entry:
            raise RuntimeErrorBase("The recorded VM identity changed; preserved.")
        return existing

    def guest(
        self,
        name: str,
        args: list[str],
        *,
        timeout: float = 60,
        cancel: threading.Event | None = None,
        input_text: str | None = None,
    ) -> ProcessResult:
        entry = next((item for item in self.discover() if item["name"] == name), None)
        if entry is None or not self.verify(entry):
            raise RuntimeErrorBase("The requested guest is not owned by this lab.")
        return self.command(
            ["shell", "--workdir=/tmp", name, *args],
            timeout=timeout,
            cancel=cancel,
            input_text=input_text,
        )

    def prepare(self, nodes: int, cancel: threading.Event) -> None:
        import time

        if nodes not in (2, 4):
            raise RuntimeErrorBase("Linux profiles require two guests or four HA guests.")
        names = [f"d{self.lab.id[:10]}-cp{n + 1}" for n in range(3 if nodes == 4 else 1)]
        names.append(f"d{self.lab.id[:10]}-worker")
        # Include the temporary SSH control socket, which is longer than the network socket.
        sockets = [self.home / "_networks/user-v2/usernet.user-v2.sock"] + [
            self.home / name / "ssh.sock.1234567890123456" for name in names
        ]
        if any(len(os.fsencode(str(path))) >= 104 for path in sockets):
            raise RuntimeErrorBase(
                "This profile path is too long for Lima sockets. Use a shorter data directory."
            )
        if shutil.disk_usage(self.root).free < 20 * 1024**3:
            raise RuntimeErrorBase(
                "Linux labs need at least 20 GiB of free disk before provisioning."
            )
        tools = Toolchain(self.tools)
        for tool in ("limactl", "lima-guestagent", "ubuntu-node", "kubectl"):
            tools.ensure(tool, cancel, self.report)
        self.home.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.home.is_symlink():
            raise RuntimeErrorBase("The private VM home is a symbolic link; preserved.")
        inventory = {entry["name"]: entry for entry in self.discover()}
        existing = self.listing()
        if any(
            (name in existing or (self.home / name).exists()) and name not in inventory
            for name in names
        ):
            raise RuntimeErrorBase("An unrecorded VM occupies a requested name; preserved.")
        if not json.loads(self.lab.resources.get("vm_intent", "[]")):
            atomic_write(
                self.root / "vm-intent.json",
                json.dumps({"lab": self.lab.id, "names": names, "created": time.time()}).encode(),
            )
            self.lab.resources["vm_intent"] = json.dumps(names)
            self.save(self.lab)
        elif json.loads(self.lab.resources["vm_intent"]) != names:
            raise RuntimeErrorBase("The requested VM topology differs from its recorded intent.")
        image = self.tools / MANIFEST["ubuntu-node"]["path"]
        for name in names:
            if name in inventory:
                current = self.verify(inventory[name])
                if current is None:
                    raise RuntimeErrorBase(
                        "A recorded guest is missing. Reset this lab to recreate it."
                    )
                if current["status"] != "Running":
                    self.require(
                        self.command(["start", name, "--timeout=5m"], timeout=330, cancel=cancel)
                    )
                continue
            self.report("Creating isolated Linux guest " + name)
            configuration: dict[str, Any] = {
                "vmType": "vz",
                "arch": "aarch64",
                "cpus": 2,
                "memory": "2GiB" if nodes == 4 else "3GiB",
                "disk": "15GiB",
                "mounts": [],
                "images": [
                    {
                        "location": str(image),
                        "arch": "aarch64",
                        "digest": "sha256:" + MANIFEST["ubuntu-node"]["sha256"],
                    }
                ],
                "containerd": {"system": False, "user": False},
                "networks": [{"lima": "user-v2"}],
                "ssh": {"loadDotSSHPubKeys": False, "forwardAgent": False},
                "propagateProxyEnv": False,
                "provision": [
                    {
                        "mode": "system",
                        "script": "#!/bin/bash\nexport DOCKYARD_GUEST=lima-"
                        + name
                        + "\n"
                        + (CONTENT / "runtime/linux/session-ready.sh").read_text(),
                    }
                ],
                "portForwards": [
                    {
                        "guestPortRange": [1, 65535],
                        "guestIP": "0.0.0.0",
                        "proto": "any",
                        "ignore": True,
                    }
                ],
            }
            forwards = configuration["portForwards"]
            if self.lab.resources.get("api_port") and name == (
                names[-1] if nodes == 4 else names[0]
            ):
                forwards.insert(
                    0,
                    {
                        "guestPort": 6444 if nodes == 4 else 6443,
                        "hostPort": int(self.lab.resources["api_port"]),
                        "hostIP": "127.0.0.1",
                        "guestIP": "0.0.0.0",
                    },
                )
            if self.lab.resources.get("port") and name == names[-1]:
                forwards.insert(
                    0,
                    {
                        "guestPort": 30080,
                        "hostPort": int(self.lab.resources["port"]),
                        "hostIP": "127.0.0.1",
                        "guestIP": "0.0.0.0",
                    },
                )
            path = self.root / (name + ".yaml")
            atomic_write(path, yaml.safe_dump(configuration).encode())
            outcome = self.command(
                ["create", "--name=" + name, str(path)], timeout=180, cancel=cancel
            )
            self.discover()
            self.require(outcome)
            self.require(self.command(["start", name, "--timeout=5m"], timeout=330, cancel=cancel))
        self.lab.resources["vm_ready"] = "true"
        self.save(self.lab)

    def kubectl(
        self,
        args: list[str],
        *,
        timeout: float = 30,
        cancel: threading.Event | None = None,
        payload: str | None = None,
        output_limit: int = 1_000_000,
    ) -> ProcessResult:
        return kubeclient.command(
            args,
            tools=self.tools,
            env=self.env,
            expected=self.lab.resources.get("kubeconfig_identity"),
            timeout=timeout,
            cancel=cancel,
            payload=payload,
            output_limit=output_limit,
        )

    def export_kubeconfig(self, cancel: threading.Event) -> None:
        primary = "d" + self.lab.id[:10] + "-cp1"
        result = self.guest(primary, ["sudo", "cat", "/etc/kubernetes/admin.conf"], cancel=cancel)
        self.require(result)
        config = yaml.safe_load(result.stdout)
        cluster = config["clusters"][0]["cluster"]
        cluster["server"] = "https://127.0.0.1:" + self.lab.resources["api_port"]
        config["contexts"][0]["context"]["namespace"] = "dispatch"
        path = Path(self.env["KUBECONFIG"])
        atomic_write(path, yaml.safe_dump(config).encode())
        self.lab.resources["kubeconfig_identity"] = kubeclient.identity(path)
        self.save(self.lab)

    def copy_to(
        self,
        name: str,
        source: Path,
        destination: str,
        *,
        cancel: threading.Event,
    ) -> None:
        entry = next((item for item in self.discover() if item["name"] == name), None)
        if entry is None or not self.verify(entry):
            raise RuntimeErrorBase("The requested guest is not owned by this lab.")
        if (
            not destination.startswith("/tmp/dockyard-" + self.lab.id)
            or ".." in Path(destination).parts
        ):
            raise RuntimeErrorBase("Guest transfers must target this lab's private temporary area.")
        if source.is_symlink() or not source.is_file():
            raise RuntimeErrorBase("The transfer source must be a regular file.")
        if not any(
            source.resolve().is_relative_to(root.resolve()) for root in (self.tools, self.root)
        ):
            raise RuntimeErrorBase(
                "Guest transfers must use app-owned lab data or verified cache files."
            )
        self.require(
            self.command(
                ["copy", str(source), name + ":" + destination], timeout=180, cancel=cancel
            )
        )

    def install_node_packages(self, cancel: threading.Event, version: str = "1.35.8") -> None:
        from dockyard.runtimes.node_packages import install

        install(self, cancel, version)

    def change(self, action: str, cancel: threading.Event) -> None:
        for entry in self.discover():
            if cancel.is_set():
                raise RuntimeErrorBase("Guest operation canceled; remaining VMs preserved.")
            current = self.verify(entry)
            if current is None:
                continue
            if action == "clean":
                args = ["delete", "--force", entry["name"]]
            elif action == "stop":
                if current["status"] == "Stopped":
                    continue
                args = ["stop", entry["name"]]
            elif action == "resume":
                if current["status"] == "Running":
                    continue
                args = ["start", entry["name"], "--timeout=5m"]
            else:
                raise ValueError("Unknown Linux lifecycle operation")
            self.require(self.command(args, timeout=330, cancel=cancel))
        if action == "clean":
            self.lab.resources["vm_inventory"] = "[]"
            self.lab.resources["vm_intent"] = "[]"
            self.lab.resources.pop("vm_ready", None)
            self.lab.resources.pop("vm_packages", None)
            self.lab.resources.pop("prepared_revision", None)
            if self.lab.resources.pop("kubeconfig_identity", None):
                (self.root / "kubeconfig").unlink(missing_ok=True)
            self.save(self.lab)

    def health(self, cancel: threading.Event) -> ProcessResult:
        outcome = self.command(["list", "--json"], cancel=cancel)
        if not outcome.ok:
            return outcome
        actual = {
            item["name"]: item
            for line in outcome.stdout.splitlines()
            if line.strip()
            for item in [json.loads(line)]
        }
        entries = self.discover()
        intended = json.loads(self.lab.resources.get("vm_intent", "[]"))
        if (
            not entries
            or len(entries) != len(intended)
            or any(actual.get(entry["name"], {}).get("status") != "Running" for entry in entries)
        ):
            return replace(
                outcome,
                returncode=1,
                stderr="One or more recorded Linux guests are stopped or missing.",
            )
        return outcome

    def fingerprint(self) -> str:
        records: list[Any] = []
        script = """import hashlib,json,os,pathlib,pwd,subprocess
paths=[pathlib.Path(p) for p in (
    '/etc/crictl.yaml','/etc/containerd/config.toml','/var/lib/kubelet/config.yaml',
    '/etc/kubernetes/kubelet.conf','/etc/kubernetes/admin.conf',
)]
paths += list(pathlib.Path('/etc/kubernetes/manifests').glob('*.yaml'))
paths += list(pathlib.Path('/etc/kubernetes/pki').rglob('*.crt'))
operator=pwd.getpwnam(os.environ['SUDO_USER']).pw_dir
paths += [pathlib.Path(operator)/'.kube/operator.conf']
files={str(p):[hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mode & 0o777]
       for p in paths if p.is_file()}
services={name:subprocess.run(
    ['systemctl','show',name,'--property=ActiveState,SubState,MainPID'],
    capture_output=True,text=True,timeout=5,
).stdout for name in ('kubelet','containerd')}
print(json.dumps({'files':files,'services':services},sort_keys=True))
"""
        for entry in self.discover():
            current = self.verify(entry)
            records.append([entry, current["status"] if current else "Missing"])
            if current and current["status"] == "Running":
                observed = self.guest(entry["name"], ["sudo", "python3", "-c", script], timeout=20)
                self.require(observed)
                records.append(json.loads(observed.stdout))
        if self.lab.resources.get("kubeconfig_identity"):
            observed = self.kubectl(
                [
                    "get",
                    "nodes,namespaces,deploy,sts,ds,pods,svc,pvc,pv,storageclasses,configmaps,secrets,roles,rolebindings,networkpolicies",
                    "-A",
                    "-o",
                    "json",
                ],
                timeout=5,
                output_limit=4_000_000,
            )
            if observed.ok and not observed.truncated:
                resources = []
                for item in json.loads(observed.stdout)["items"]:
                    metadata = item["metadata"]
                    resources.append(
                        [
                            item["kind"],
                            metadata.get("namespace", ""),
                            metadata["name"],
                            metadata["uid"],
                            metadata.get("generation"),
                            metadata.get("labels", {}),
                            item.get("spec", {}),
                            item.get("data", {}),
                            item.get("rules", []),
                            item.get("roleRef", {}),
                            item.get("subjects", []),
                        ]
                    )
                records.append(sorted(resources, key=lambda item: item[:3]))
            else:
                records.append("Kubernetes API unavailable")
        return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
