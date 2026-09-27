"""Portable host contracts, including Windows-to-WSL argument boundaries."""

import json
import os
import re
from contextlib import suppress
from pathlib import Path

import pytest

from dockyard import host, terminals
from dockyard.catalog import CONTENT
from dockyard.models import Lab, Runtime
from dockyard.process import ProcessResult
from dockyard.service import Service
from dockyard.store import timestamp
from dockyard.toolchain import platform_manifest


@pytest.mark.parametrize(
    "system,machine,key",
    [
        ("Darwin", "arm64", "darwin-arm64"),
        ("Linux", "aarch64", "linux-arm64"),
        ("Linux", "x86_64", "linux-amd64"),
        ("Linux", "AMD64", "linux-amd64"),
    ],
)
def test_supported_platforms(monkeypatch, system, machine, key):
    monkeypatch.setattr(host.platform, "system", lambda: system)
    monkeypatch.setattr(host.platform, "machine", lambda: machine)
    monkeypatch.setattr(host.platform, "release", lambda: "6.8.0-generic")
    assert host.platform_key() == key
    assert host.vm_type() == ("vz" if system == "Darwin" else "qemu")


def test_wsl_two_required(monkeypatch):
    monkeypatch.setattr(host.platform, "system", lambda: "Linux")
    monkeypatch.setattr(host.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(host.platform, "release", lambda: "4.4.0-Microsoft")
    with pytest.raises(ValueError, match="WSL 1"):
        host.platform_key()
    monkeypatch.setattr(host.platform, "release", lambda: "6.6.87.2-microsoft-standard-WSL2")
    assert host.is_wsl() and host.platform_key() == "linux-amd64"


def test_data_paths_preserve_mac_and_follow_xdg(monkeypatch, tmp_path):
    monkeypatch.delenv("DOCKYARD_DATA", raising=False)
    monkeypatch.setattr(host.platform, "system", lambda: "Darwin")
    assert host.default_directory() == Path.home() / "Library/Application Support/Dockyard"
    monkeypatch.setattr(host.platform, "system", lambda: "Linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "private data"))
    assert host.default_directory() == tmp_path / "private data/dockyard"
    monkeypatch.setenv("XDG_DATA_HOME", "relative")
    assert host.default_directory() == Path.home() / ".local/share/dockyard"
    monkeypatch.setenv("DOCKYARD_DATA", str(tmp_path / "override"))
    assert host.default_directory() == tmp_path / "override"


def test_native_linux_requires_tools_and_kvm(monkeypatch):
    monkeypatch.setattr(host.platform, "system", lambda: "Linux")
    monkeypatch.setattr(host.shutil, "which", lambda name: None)
    assert "qemu-system-" in host.native_blocker()
    monkeypatch.setattr(host.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(host.os, "access", lambda *args: False)
    assert "/dev/kvm" in host.native_blocker()
    monkeypatch.setattr(host.os, "access", lambda *args: True)
    assert host.native_blocker() is None


@pytest.mark.parametrize("key", ["darwin-arm64", "linux-arm64", "linux-amd64"])
def test_tool_and_package_pins_cover_each_architecture(key):
    manifest = platform_manifest(key)
    for name, entry in manifest.items():
        assert re.fullmatch("[a-f0-9]{64}", entry["sha256"]), name
        assert entry["url"].startswith("https://"), name
    arch = key.split("-")[1]
    for version in ("1.34.12", "1.35.8"):
        suffix = "-amd64" if arch == "amd64" else ""
        record = json.loads(
            (CONTENT / f"runtime/linux/packages-{version}{suffix}.json").read_text()
        )
        assert record["base_image_sha256"] == manifest["ubuntu-node"]["sha256"]
        assert len(record["packages"]) >= 20
        assert all(name.endswith((f"_{arch}.deb", "_all.deb")) for name in record["packages"])


def test_wsl_terminal_keeps_distribution_paths_and_arguments(monkeypatch, tmp_path):
    service = Service(tmp_path)
    lab = Lab(
        id="e" * 32,
        unit_id="m01-processes",
        revision=1,
        runtime=Runtime.DOCKER,
        state="ready",
        workspace=str(tmp_path / "space and $literal/workspace"),
        created_at=timestamp(),
        updated_at=timestamp(),
        resources={"port": "32123", "docker_endpoint": "unix:///var/run/docker.sock"},
    )
    Path(lab.workspace).mkdir(parents=True)
    service.store.save_lab(lab)
    monkeypatch.setattr(
        terminals,
        "available",
        lambda: [
            terminals.Terminal(
                "wezterm-windows", "WezTerm (Windows)", "/mnt/c/Program Files/WezTerm/wezterm.exe"
            )
        ],
    )
    monkeypatch.setattr(host, "is_wsl", lambda: True)
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu Test")
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        return ProcessResult(tuple(args), 0, "1", "", 0)

    monkeypatch.setattr("dockyard.terminals.run", run)
    service.open_terminal(lab.unit_id)
    argv = calls[0]
    assert argv[argv.index("--domain-name") + 1] == "local"
    assert argv[argv.index("--distribution") + 1] == "Ubuntu Test"
    assert argv[argv.index("--cd") + 1] == lab.workspace
    assert "bash" not in argv and "-c" not in argv
    assert service.environment(lab)["DOCKER_DEFAULT_PLATFORM"] == "linux/" + host.architecture()
    assert service.environment(lab)["DOCKYARD_ARCH"] == host.architecture()


def test_private_bash_startup_runs_in_a_real_pty(tmp_path):
    import pty
    import select
    import shutil
    import signal
    import time

    service = Service(tmp_path)
    workspace = tmp_path / "workspace with spaces"
    workspace.mkdir()
    lab = Lab(
        id="f" * 32,
        unit_id="m01-processes",
        revision=1,
        runtime=Runtime.DOCKER,
        state="ready",
        workspace=str(workspace),
        created_at=timestamp(),
        updated_at=timestamp(),
    )
    rc = service.write_shell_rc(lab)
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(workspace)
        os.execv(
            shutil.which("bash"), ["bash", "--noprofile", "--rcfile", str(rc / ".bashrc"), "-i"]
        )
    output = b""
    try:
        os.write(fd, b"printf 'PWD=%s\\n' \"$PWD\"; exit\n")
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if select.select([fd], [], [], 0.1)[0]:
                try:
                    data = os.read(fd, 65536)
                except OSError:
                    break
                if not data:
                    break
                output += data
        assert b"dockyard m01-processes ffffffff" in output
        assert ("PWD=" + str(workspace)).encode() in output
    finally:
        os.close(fd)
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)


def test_missing_docker_plugins_have_actionable_diagnostics(monkeypatch):
    calls = []

    def execute(args, **kwargs):
        calls.append(args)
        return ProcessResult(tuple(args), 1 if args[1] == "buildx" else 0, "", "", 0)

    monkeypatch.setattr("dockyard.process.run", execute)
    assert host.docker_plugin_blocker({}) == (
        "Install Docker's buildx plugins before preparing labs."
    )
    assert calls == [["docker", "buildx", "version"], ["docker", "compose", "version"]]
