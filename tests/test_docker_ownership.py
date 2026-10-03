"""Ownership checks compare Docker creation times with the engine's own clock."""

import json

import pytest

from dockyard.models import Lab, Runtime
from dockyard.process import ProcessResult
from dockyard.runtimes.docker import LABEL, DockerRuntime, RuntimeErrorBase

HOST_CREATED = "2026-10-03T05:09:22.338101+00:00"
# After the computer slept, the Docker VM clock still read about fifteen minutes behind.
ENGINE_CLOCK = "2026-10-03T04:54:50.120000000Z"


def runtime_with_network(created: str, resources: dict[str, str]) -> DockerRuntime:
    lab = Lab(
        id="lab-one",
        unit_id="i05-readiness-port",
        revision=1,
        runtime=Runtime.KUBERNETES,
        state="preparing",
        workspace="/unused",
        created_at=HOST_CREATED,
        updated_at=HOST_CREATED,
        resources=resources,
    )
    runtime = DockerRuntime(lab, {}, lambda lab: None)

    def command(args, **_):
        if args[1] == "ls":
            listed = "net-one" if args[0] == "network" else ""
            return ProcessResult(tuple(args), 0, listed, "", 0)
        body = {"Id": "net-one", "Created": created, "Labels": {LABEL: "lab-one"}}
        return ProcessResult(tuple(args), 0, json.dumps([body]), "", 0)

    runtime.command = command  # type: ignore[method-assign]
    return runtime


def test_a_resource_stamped_by_a_lagging_engine_clock_is_still_owned():
    runtime = runtime_with_network("2026-10-03T04:54:52.976664388Z", {"docker_clock": ENGINE_CLOCK})
    assert [item["id"] for item in runtime.discover()] == ["net-one"]


def test_a_resource_older_than_the_engine_reading_is_preserved():
    runtime = runtime_with_network("2026-10-03T04:50:00.000000000Z", {"docker_clock": ENGINE_CLOCK})
    with pytest.raises(RuntimeErrorBase, match="predates this lab"):
        runtime.discover()


def test_labs_recorded_without_an_engine_reading_keep_host_time():
    runtime = runtime_with_network("2026-10-03T04:54:52.976664388Z", {})
    with pytest.raises(RuntimeErrorBase, match="predates this lab"):
        runtime.discover()
    assert [
        item["id"] for item in runtime_with_network("2026-10-03T05:09:23.000000000Z", {}).discover()
    ] == ["net-one"]
