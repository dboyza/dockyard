"""A check waits while a restarted kubelet has not yet relisted the Pods bound to its node."""

import json
import threading
from pathlib import Path

from dockyard.models import Lab, Runtime
from dockyard.process import ProcessResult
from dockyard.runtimes import linux
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.store import timestamp


def pod(name: str, node: str, phase: str = "Running", **metadata) -> dict:
    return {
        "metadata": {"namespace": "dispatch", "name": name, **metadata},
        "spec": {"nodeName": node},
        "status": {"phase": phase},
    }


class Cluster:
    """Answers kubectl like a cluster whose worker kubelet relists its Pods after a delay."""

    def __init__(self, relisted_after: int, kubelet_answers: bool = True):
        self.relisted_after, self.kubelet_answers = relisted_after, kubelet_answers
        self.listings = 0
        self.api = [
            pod("db-0", "worker"),
            pod("old", "worker", phase="Succeeded"),
            pod("leaving", "worker", deletionTimestamp="2026-11-16T00:00:00Z"),
            pod("dispatch", "cp"),
        ]

    def __call__(self, args: list[str], **_) -> ProcessResult:
        def answer(body: object, code: int = 0) -> ProcessResult:
            return ProcessResult(tuple(args), code, json.dumps(body), "", 0.1)

        if args[:2] == ["get", "pods"]:
            return answer({"items": self.api})
        if args[:2] == ["get", "nodes"]:
            ready = {"type": "Ready", "status": "True"}
            nodes = [
                {"metadata": {"name": n}, "status": {"conditions": [ready]}}
                for n in ("cp", "worker")
            ]
            return answer({"items": nodes})
        node = args[2].split("/")[4]
        if node == "worker":
            if not self.kubelet_answers:
                return answer({}, 1)
            self.listings += 1
            known = [pod("db-0", node)] if self.listings > self.relisted_after else None
            return answer({"items": known})
        return answer({"items": [pod("dispatch", node)]})


def runtime(tmp_path: Path, cluster: Cluster, monkeypatch) -> LinuxRuntime:
    lab = Lab(
        id="a" * 32,
        unit_id="m25-benchmark",
        revision=1,
        runtime=Runtime.LINUX,
        state="ready",
        workspace=str(tmp_path / "labs/example/workspace"),
        created_at=timestamp(),
        updated_at=timestamp(),
        resources={"kubeconfig_identity": "owned"},
    )
    result = LinuxRuntime(lab, {}, lambda _: None, tmp_path / "tools")
    monkeypatch.setattr(result, "kubectl", cluster)
    clock = iter(range(0, 10_000, 2))
    monkeypatch.setattr(linux.time, "monotonic", lambda: next(clock))
    return result


class NoWait(threading.Event):
    def wait(self, timeout: float | None = None) -> bool:
        return False


def test_a_check_waits_until_the_kubelet_relists_its_pods(tmp_path, monkeypatch):
    cluster = Cluster(relisted_after=3)
    runtime(tmp_path, cluster, monkeypatch).await_node_agents(NoWait())
    assert cluster.listings == 4


def test_the_wait_is_bounded_when_the_kubelet_never_catches_up(tmp_path, monkeypatch):
    cluster = Cluster(relisted_after=10_000)
    runtime(tmp_path, cluster, monkeypatch).await_node_agents(NoWait(), limit=60)
    assert 0 < cluster.listings <= 30


def test_a_kubelet_that_does_not_answer_is_left_to_the_check(tmp_path, monkeypatch):
    cluster = Cluster(relisted_after=10_000, kubelet_answers=False)
    runtime(tmp_path, cluster, monkeypatch).await_node_agents(NoWait())
    assert cluster.listings == 0
