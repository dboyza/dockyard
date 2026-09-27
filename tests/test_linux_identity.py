"""VM lifecycle must refuse replaced disks, changed mounts, and unowned names."""

import json
from pathlib import Path

import pytest
import yaml

from dockyard import host
from dockyard.models import Lab, Runtime
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.store import timestamp


def fixture(tmp_path: Path):
    lab = Lab(
        id="a" * 32,
        unit_id="m19-runtime",
        revision=1,
        runtime=Runtime.LINUX,
        state="ready",
        workspace=str(tmp_path / "labs/example/workspace"),
        created_at=timestamp(),
        updated_at=timestamp(),
        resources={},
    )
    runtime = LinuxRuntime(
        lab,
        {"LIMA_HOME": "/unrelated", "SSH": "unrelated-helper", "KUBECONFIG": "/unrelated/config"},
        lambda _: None,
        tmp_path / "tools",
    )
    directory = runtime.home / "owned"
    directory.mkdir(parents=True)
    (directory / "lima.yaml").write_text(
        yaml.safe_dump({"vmType": host.vm_type(), "arch": host.guest_architecture(), "mounts": []})
    )
    (directory / "disk").write_bytes(b"owned disk")
    entry = runtime.identity("owned")
    lab.resources["vm_inventory"] = json.dumps([entry])
    return runtime, entry, directory


def test_vm_identity_preserves_replaced_disk_and_changed_mounts(tmp_path, monkeypatch):
    runtime, entry, directory = fixture(tmp_path)
    monkeypatch.setattr(
        runtime, "listing", lambda: {"owned": {"name": "owned", "status": "Stopped"}}
    )
    assert runtime.env["LIMA_HOME"] == str(runtime.home)
    assert runtime.env["SSH"] == "/usr/bin/ssh"
    assert runtime.env["KUBECONFIG"] == str(runtime.root / "kubeconfig")
    assert runtime.verify(entry)["status"] == "Stopped"
    replacement = directory / "replacement"
    replacement.write_bytes(b"different VM")
    replacement.replace(directory / "disk")
    with pytest.raises(RuntimeErrorBase, match="identity changed"):
        runtime.verify(entry)
    assert (directory / "disk").read_bytes() == b"different VM"
    (directory / "lima.yaml").write_text(
        yaml.safe_dump(
            {
                "vmType": host.vm_type(),
                "arch": host.guest_architecture(),
                "mounts": [{"location": "~"}],
            }
        )
    )
    with pytest.raises(RuntimeErrorBase, match="no-mount"):
        runtime.identity("owned")


def test_vm_unrecorded_name_is_not_adopted(tmp_path, monkeypatch):
    runtime, entry, directory = fixture(tmp_path)
    runtime.lab.resources["vm_inventory"] = "[]"
    monkeypatch.setattr(
        runtime, "listing", lambda: {"owned": {"name": "owned", "status": "Stopped"}}
    )
    assert runtime.discover() == []
    assert directory.exists()
    with pytest.raises(RuntimeErrorBase, match="not owned"):
        runtime.guest("owned", ["true"])


def test_long_ssh_socket_path_is_rejected_before_guest_creation(tmp_path, monkeypatch):
    import threading

    runtime, _, _ = fixture(tmp_path)
    runtime.home = tmp_path / ("long-profile-" * 9) / "vms"
    monkeypatch.setattr(
        runtime, "command", lambda *a, **kw: pytest.fail("No guest command expected")
    )
    with pytest.raises(RuntimeErrorBase, match="too long for Lima sockets"):
        runtime.prepare(2, threading.Event())
