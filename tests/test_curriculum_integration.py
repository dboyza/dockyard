"""Authoring gate: fail the intended starter, run the reference, observe actual behavior."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from dockyard.catalog import Catalog
from dockyard.models import Runtime
from dockyard.process import run
from dockyard.service import Service
from dockyard.workspace import write_files

UNITS = list(Catalog().units)
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("DOCKYARD_INTEGRATION") != "1", reason="opt-in real runtimes"
    ),
]


@pytest.mark.parametrize("unit_id", UNITS, ids=UNITS)
def test_authored_reference_repairs_its_actual_starter(tmp_path, unit_id):
    if Catalog().get(unit_id).runtime == Runtime.LINUX:
        # Native providers use Unix sockets whose paths must stay below the macOS limit.
        with tempfile.TemporaryDirectory(prefix="dy-course-", dir="/private/tmp") as temporary:
            assert_reference(Path(temporary), unit_id)
    else:
        assert_reference(tmp_path, unit_id)


def assert_reference(tmp_path, unit_id):
    service = Service(tmp_path)
    unit = service.catalog.get(unit_id)
    try:
        service.perform(unit_id, "prepare")
        deadline = time.monotonic() + 30
        while True:
            starter = service.perform(unit_id, "check")
            if starter["status"] != "stale" or time.monotonic() >= deadline:
                break
            time.sleep(0.5)
        assert starter["status"] == "fail", starter
        for criterion_id in unit.starter_failure_checks:
            observation = next(
                item for item in starter["evidence"] if item["criterion"] == criterion_id
            )
            assert observation["status"] == "fail", observation
            criterion = next(item for item in unit.checks if item.id == criterion_id)
            if any(arg.startswith("dockyard.probes.") for arg in criterion.command.args):
                assert observation["observed"].strip() == "false", observation
        lab = service.store.lab(unit_id)
        assert lab is not None
        workspace = Path(lab.workspace)
        write_files(workspace, unit.reference, overwrite=True)
        solution = run(
            ["/bin/sh", "run.sh"], cwd=workspace, env=service.environment(lab), timeout=600
        )
        assert solution.ok, solution.stdout + solution.stderr
        deadline = time.monotonic() + 30
        while True:
            observed = service.perform(unit_id, "check")
            if observed["status"] == "pass" or time.monotonic() > deadline:
                break
            time.sleep(0.25)
        assert observed["status"] == "pass", observed
        assert observed["independent"] == (unit.kind != "lesson")
        assert service.store.progress()[unit_id]["practiced"] == 1
        if unit_id == "m20-ha":
            assert_ha_alternative_and_shortcut(service, unit_id)
        if unit_id == "m21-drain":
            assert_drain_alternative_and_shortcut(service, unit_id)
    finally:
        service.perform(unit_id, "clean")


def assert_drain_alternative_and_shortcut(service, unit_id):
    """Equivalent eviction budgets pass; returning the target to scheduling does not."""
    import json

    lab = service.store.lab(unit_id)
    runtime = service.runtime(lab)
    runtime.require(
        runtime.kubectl(
            [
                "patch",
                "pdb",
                "dispatch-maintenance",
                "--type=merge",
                "-p",
                json.dumps({"spec": {"minAvailable": None, "maxUnavailable": 1}}),
            ]
        )
    )
    deadline = time.monotonic() + 30
    while True:
        observed = service.perform(unit_id, "check")
        if observed["status"] == "pass" or time.monotonic() >= deadline:
            break
        time.sleep(0.5)
    assert observed["status"] == "pass", observed
    runtime.require(runtime.kubectl(["uncordon", "lima-d" + lab.id[:10] + "-worker2"]))
    observed = service.perform(unit_id, "check")
    assert observed["status"] != "pass", observed
    drained = next(
        item for item in observed["evidence"] if item["criterion"] == "maintenance-drained"
    )
    assert drained["status"] == "fail" and drained["observed"] == "false", drained


def assert_ha_alternative_and_shortcut(service, unit_id):
    """One healthy backend is valid; restoring the primary does not demonstrate failover."""
    from dockyard.runtimes.native_cluster import load_balancer_configuration

    lab = service.store.lab(unit_id)
    runtime = service.runtime(lab)
    names = [entry["name"] for entry in runtime.discover()]
    runtime.require(
        runtime.guest(
            names[-1],
            ["sudo", "tee", "/etc/haproxy/haproxy.cfg"],
            input_text=load_balancer_configuration([names[2]]),
        )
    )
    runtime.require(runtime.guest(names[-1], ["sudo", "systemctl", "reload", "haproxy"]))
    deadline = time.monotonic() + 30
    while True:
        observed = service.perform(unit_id, "check")
        if observed["status"] == "pass" or time.monotonic() >= deadline:
            break
        time.sleep(0.5)
    assert observed["status"] == "pass", observed
    for component in ("kube-apiserver", "etcd"):
        runtime.require(
            runtime.guest(
                names[0],
                [
                    "sudo",
                    "mv",
                    "/var/lib/dockyard/ha-outage/" + component + ".yaml",
                    "/etc/kubernetes/manifests/" + component + ".yaml",
                ],
            )
        )
    import json

    deadline = time.monotonic() + 90
    while True:
        running = runtime.guest(names[0], ["sudo", "crictl", "ps", "-o", "json"])
        runtime.require(running)
        components = {
            item.get("labels", {}).get("io.kubernetes.container.name")
            for item in json.loads(running.stdout)["containers"]
        }
        if {"kube-apiserver", "etcd"} <= components:
            break
        assert time.monotonic() < deadline, components
        time.sleep(1)
    observed = service.perform(unit_id, "check")
    assert observed["status"] != "pass", observed
    outage = next(item for item in observed["evidence"] if item["criterion"] == "bootstrap-outage")
    assert outage["status"] == "fail" and outage["observed"] == "false", outage
