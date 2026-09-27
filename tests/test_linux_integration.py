"""Real native guests, peer networking, identity preservation, and lifecycle cleanup."""

import json
import os
import socket
import tempfile
import threading
import time
import urllib.request
import uuid
from pathlib import Path

import pytest

from dockyard import host
from dockyard.catalog import CONTENT
from dockyard.models import Lab, Runtime
from dockyard.process import run
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
    with tempfile.TemporaryDirectory(prefix="dy-vm-", dir=host.temporary_root()) as temporary:
        profile = Path(temporary)
        service = Service(profile)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            api_port = listener.getsockname()[1]
        with socket.socket() as listener, socket.socket(type=socket.SOCK_DGRAM) as datagram:
            listener.bind(("127.0.0.1", 0))
            isolated_port = listener.getsockname()[1]
            datagram.bind(("127.0.0.1", isolated_port))
        lab = Lab(
            id=uuid.uuid4().hex,
            unit_id="m19-runtime",
            revision=1,
            runtime=Runtime.LINUX,
            state="preparing",
            workspace=str(profile / "labs/guest-proof/workspace"),
            created_at=timestamp(),
            updated_at=timestamp(),
            resources={"api_port": str(api_port)},
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
                assert observed.ok and observed.stdout.strip() == host.guest_architecture()
            server = f"""import http.server,socket,threading
class IPv6Server(http.server.ThreadingHTTPServer):
    address_family=socket.AF_INET6
for port in (6443,{isolated_port}):
    handler=IPv6Server(('::',port),http.server.SimpleHTTPRequestHandler)
    threading.Thread(target=handler.serve_forever,daemon=True).start()
udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
udp.bind(('0.0.0.0',{isolated_port}))
while True:
    data,peer=udp.recvfrom(4096)
    udp.sendto(data,peer)
"""
            started = runtime.guest(
                names[0],
                [
                    "sudo",
                    "systemd-run",
                    "--unit=dockyard-network-proof",
                    "/usr/bin/python3",
                    "-c",
                    server,
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
                    "http://lima-" + names[0] + f".internal:{isolated_port}/",
                ],
            )
            assert received.ok and "Directory listing" in received.stdout
            # An explicit API forward must work while unrelated TCP and UDP listeners stay private.
            deadline = time.monotonic() + 20
            while True:
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{api_port}/", timeout=2
                    ) as response:
                        assert b"Directory listing" in response.read()
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.2)
            with (
                pytest.raises(OSError),
                socket.create_connection(("127.0.0.1", isolated_port), timeout=1),
            ):
                pytest.fail("An unrelated guest TCP listener was forwarded")
            with socket.socket(type=socket.SOCK_DGRAM) as datagram:
                datagram.settimeout(1)
                datagram.sendto(b"unforwarded-native-port", ("127.0.0.1", isolated_port))
                with pytest.raises((TimeoutError, ConnectionRefusedError)):
                    datagram.recv(4096)
            # A frozen login manager reproduces the observed D-Bus failure without changing
            # SSH authentication or the Kubernetes services learners will administer.
            initial = runtime.guest(
                names[0], ["systemctl", "show", "systemd-logind", "-p", "MainPID", "--value"]
            )
            runtime.require(initial)
            runtime.require(
                runtime.guest(names[0], ["sudo", "kill", "-STOP", initial.stdout.strip()])
            )
            recovered = runtime.guest(
                names[0],
                ["sudo", "env", "DOCKYARD_GUEST=lima-" + names[0], "bash", "-s"],
                input_text=(CONTENT / "runtime/linux/session-ready.sh").read_text(),
                timeout=30,
            )
            assert recovered.ok, recovered.stderr
            fresh = run(
                [
                    "/usr/bin/ssh",
                    "-F",
                    str(runtime.home / names[0] / "ssh.config"),
                    "-o",
                    "ControlMaster=no",
                    "-o",
                    "ControlPath=none",
                    "lima-" + names[0],
                    "printf",
                    "fresh-session-ready",
                ],
                env=runtime.env,
                timeout=10,
            )
            assert fresh.ok and fresh.stdout == "fresh-session-ready", fresh.stderr
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
    with tempfile.TemporaryDirectory(prefix="dy-offline-", dir=host.temporary_root()) as temporary:
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
