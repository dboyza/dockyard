"""Docker observations report a missing resource as an unmet outcome, not a crash."""

import json
import sys
import tarfile

import pytest

from dockyard.catalog import Catalog
from dockyard.probes import docker
from dockyard.process import ProcessResult


def test_every_authored_docker_criterion_reads_a_declared_outcome():
    for unit in Catalog().units.values():
        for criterion in unit.checks:
            args = criterion.command.args
            if "dockyard.probes.docker" in args:
                probe = args[args.index("dockyard.probes.docker") + 1]
                assert str(criterion.json_path[0]) in docker.OUTCOMES[probe], (unit.id, probe)


def test_missing_container_reports_every_outcome_unmet(monkeypatch, capsys):
    missing = ProcessResult((), 1, "", "Error response from daemon: No such container: x", 0.0)
    monkeypatch.setattr(docker, "run", lambda *args, **kwargs: missing)
    monkeypatch.setattr(sys, "argv", ["probe", "network"])
    monkeypatch.setenv("DOCKYARD_CONTAINER", "x")
    monkeypatch.setenv("DOCKYARD_LAB", "lab")
    docker.main()
    report = json.loads(capsys.readouterr().out)
    assert all(report[key] is False for key in docker.OUTCOMES["network"])
    assert "No such container" in report["_details"]["owned"]["not_observed"]


def test_other_docker_errors_still_fail_the_observation(monkeypatch, capsys):
    denied = ProcessResult((), 1, "", "permission denied while trying to connect", 0.0)
    monkeypatch.setattr(docker, "run", lambda *args, **kwargs: denied)
    monkeypatch.setattr(sys, "argv", ["probe", "network"])
    monkeypatch.setenv("DOCKYARD_CONTAINER", "x")
    monkeypatch.setenv("DOCKYARD_LAB", "lab")
    with pytest.raises(SystemExit):
        docker.main()
    assert "observation_error" in json.loads(capsys.readouterr().out)


def filesystem(*entries):
    """Tar members for an exported filesystem: (name, target) links, or plain file names."""
    members = {}
    for entry in entries:
        name, target = entry if isinstance(entry, tuple) else (entry, None)
        member = tarfile.TarInfo(name)
        if target is not None:
            member.type, member.linkname = tarfile.SYMTYPE, target
        members[name] = member
    return members


def test_a_shell_counts_only_while_its_link_leads_to_a_program():
    alpine = filesystem("bin/busybox", ("bin/sh", "/bin/busybox"), ("bin/ash", "busybox"))
    assert docker.runnable(alpine, "bin/sh") and docker.runnable(alpine, "bin/ash")
    # Deleting BusyBox leaves its links pointing at nothing, which cannot run.
    del alpine["bin/busybox"]
    assert not docker.runnable(alpine, "bin/sh") and not docker.runnable(alpine, "bin/ash")


def test_link_resolution_follows_relative_chains_and_stops_on_loops():
    chain = filesystem("usr/bin/dash", ("bin/dash", "../usr/bin/dash"), ("bin/sh", "dash"))
    assert docker.runnable(chain, "bin/sh")
    loop = filesystem(("bin/sh", "ash"), ("bin/ash", "sh"))
    assert not docker.runnable(loop, "bin/sh")
