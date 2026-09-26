"""Real native guests, peer networking, identity preservation, and lifecycle cleanup."""

import json
import os
import tempfile
import threading
import uuid
from pathlib import Path

import pytest

from dockyard.models import Lab, Runtime
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.service import Service
from dockyard.store import timestamp

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("DOCKYARD_VM_INTEGRATION") != "1", reason="opt-in real Linux VMs"
    ),
]


def test_linux_guests_network_resume_and_preserve_identity():
    # Short profile paths are required by the platform's Unix socket length limit.
    with tempfile.TemporaryDirectory(prefix="dy-vm-", dir="/private/tmp") as temporary:
        profile = Path(temporary)
        service = Service(profile)
        lab = Lab(
            id=uuid.uuid4().hex,
            unit_id="m19-runtime",
            revision=1,
            runtime=Runtime.LINUX,
            state="preparing",
            workspace=str(profile / "labs/guest-proof/workspace"),
            created_at=timestamp(),
            updated_at=timestamp(),
            resources={},
        )
        Path(lab.workspace).mkdir(parents=True)
        runtime = LinuxRuntime(lab, service.environment(), service.store.save_lab, service.tools)
        cancel = threading.Event()
        try:
            runtime.prepare(2, cancel)
            entries = runtime.discover()
            assert len(entries) == 2
            names = [entry["name"] for entry in entries]
            for entry in entries:
                assert runtime.verify(entry)["status"] == "Running"
                observed = runtime.guest(entry["name"], ["uname", "-m"])
                assert observed.ok and observed.stdout.strip() == "aarch64"
            started = runtime.guest(
                names[0],
                [
                    "sudo",
                    "systemd-run",
                    "--unit=dockyard-network-proof",
                    "/usr/bin/python3",
                    "-m",
                    "http.server",
                    "8097",
                    "--bind",
                    "0.0.0.0",
                ],
            )
            assert started.ok, started.stderr
            received = runtime.guest(
                names[1],
                [
                    "curl",
                    "--fail",
                    "--retry",
                    "8",
                    "--retry-connrefused",
                    "--retry-delay",
                    "1",
                    "--max-time",
                    "3",
                    "http://lima-" + names[0] + ".internal:8097/",
                ],
            )
            assert received.ok and "Directory listing" in received.stdout
            runtime.change("stop", cancel)
            assert all(runtime.verify(entry)["status"] == "Stopped" for entry in entries)
            runtime.change("resume", cancel)
            assert runtime.discover() == entries
            assert all(runtime.verify(entry)["status"] == "Running" for entry in entries)
            configuration = runtime.home / names[0] / "lima.yaml"
            original = configuration.read_bytes()
            try:
                configuration.write_bytes(original + b"\n# changed outside Dockyard\n")
                with pytest.raises(RuntimeErrorBase, match="identity changed"):
                    runtime.change("stop", cancel)
            finally:
                configuration.write_bytes(original)
        finally:
            runtime.change("clean", cancel)
        assert json.loads(lab.resources["vm_inventory"]) == []
        assert not any(runtime.home.glob("d*-cp*"))
        assert not any(runtime.home.glob("d*-worker"))


@pytest.mark.parametrize("version,cri_version", [("1.35.8", "1.35.0"), ("1.34.12", "1.34.0")])
def test_native_prerequisites_install_with_unusable_package_proxies(version, cri_version):
    with tempfile.TemporaryDirectory(prefix="dy-offline-", dir="/private/tmp") as temporary:
        profile = Path(temporary)
        service = Service(profile)
        lab = Lab(
            id=uuid.uuid4().hex,
            unit_id="m19-runtime",
            revision=1,
            runtime=Runtime.LINUX,
            state="preparing",
            workspace=str(profile / "labs/guest-proof/workspace"),
            created_at=timestamp(),
            updated_at=timestamp(),
            resources={},
        )
        Path(lab.workspace).mkdir(parents=True)
        runtime = LinuxRuntime(lab, service.environment(), service.store.save_lab, service.tools)
        cancel = threading.Event()
        try:
            runtime.prepare(2, cancel)
            entries = runtime.discover()
            for entry in entries:
                disabled = runtime.guest(
                    entry["name"],
                    ["sudo", "tee", "/etc/apt/apt.conf.d/99dockyard-offline"],
                    input_text='Acquire::http::Proxy "http://127.0.0.1:9";\nAcquire::https::Proxy "http://127.0.0.1:9";\n',
                )
                assert disabled.ok, disabled.stderr
            runtime.install_node_packages(cancel, version)
            for entry in entries:
                observed_version = runtime.guest(
                    entry["name"], ["kubeadm", "version", "-o", "short"]
                )
                assert observed_version.ok and observed_version.stdout.strip() == "v" + version
                observed_version = runtime.guest(entry["name"], ["crictl", "--version"])
                assert observed_version.ok and cri_version in observed_version.stdout
                actual = runtime.guest(entry["name"], ["sudo", "crictl", "info"])
                assert actual.ok, actual.stderr
                info = json.loads(actual.stdout)
                assert any(
                    c["type"] == "RuntimeReady" and c["status"]
                    for c in info["status"]["conditions"]
                )
                assert (
                    info["config"]["containerd"]["runtimes"]["runc"]["options"]["SystemdCgroup"]
                    is True
                )
            assert len(json.loads(lab.resources["vm_packages"])) == 2
        finally:
            runtime.change("clean", cancel)
