import threading
from types import SimpleNamespace

import pytest

from dockyard.process import ProcessResult
from dockyard.runtimes.kubernetes import KubernetesRuntime, parse_time, stale_pods

NODE = "dockyard-example-control-plane"
STARTS = {NODE: parse_time("2026-09-28T02:58:10.123456789Z")}


def pod(name, namespace="dispatch", started=None, ready=True, phase="Running", waiting=False):
    state = (
        {"waiting": {"reason": "CrashLoopBackOff"}}
        if waiting
        else {"running": {"startedAt": started}}
    )
    return {
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"nodeName": NODE},
        "status": {
            "phase": phase,
            "containerStatuses": [{"state": state}],
            "conditions": [{"type": "Ready", "status": "True" if ready else "False"}],
        },
    }


def test_container_running_since_before_node_restart_is_stale():
    assert stale_pods([pod("api", started="2026-09-28T02:53:34Z")], STARTS) == ["dispatch/api"]


def test_container_restarted_after_node_start_is_current():
    assert stale_pods([pod("api", started="2026-09-28T02:58:27Z")], STARTS) == []


def test_unready_application_pod_is_not_waited_for():
    # A lab starter can be broken on purpose; only its stale report matters.
    assert stale_pods([pod("worker", ready=False, waiting=True)], STARTS) == []


def test_unready_system_pod_is_waited_for():
    system = pod("coredns", namespace="kube-system", started="2026-09-28T02:58:30Z", ready=False)
    assert stale_pods([system], STARTS) == ["kube-system/coredns"]


def test_finished_pods_are_ignored():
    done = pod("audit", started="2026-09-28T01:00:00Z", phase="Succeeded")
    assert stale_pods([done], STARTS) == []


def test_pod_subnet_avoids_docker_default_pool_networks():
    from dockyard.runtimes.kubernetes import choose_pod_subnet

    assert choose_pod_subnet(["192.168.96.0/20"]) == "10.244.0.0/16"
    assert choose_pod_subnet(["172.19.0.0/16"]) == "10.244.0.0/16"
    assert choose_pod_subnet(["10.244.0.0/16"]) == "10.200.0.0/16"


def test_pod_subnet_reports_when_every_range_overlaps():
    import pytest

    from dockyard.runtimes.docker import RuntimeErrorBase
    from dockyard.runtimes.kubernetes import choose_pod_subnet

    with pytest.raises(RuntimeErrorBase, match="overlaps"):
        choose_pod_subnet(["10.0.0.0/8", "100.64.0.0/10"])


@pytest.mark.parametrize(
    ("resources", "daemonset"), [({"cni": "kindnet"}, "kindnet"), ({}, "calico-node")]
)
def test_resume_waits_for_the_network_plugin_the_cluster_was_made_with(
    tmp_path, resources, daemonset
):
    # Clusters made before kind labs switched to kindnet still run Calico.
    lab = SimpleNamespace(id="0" * 32, workspace=str(tmp_path / "workspace"), resources=resources)
    runtime = KubernetesRuntime(lab, {}, lambda lab: None, tmp_path)
    waited = []

    def kubectl(args, **kwargs):
        if args[:2] == ["rollout", "status"]:
            waited.append(args[2])
        return ProcessResult(tuple(args), 0, "", "", 0.0)

    runtime.kubectl = kubectl
    runtime.wait_ready(threading.Event())
    assert waited == [f"daemonset/{daemonset}", "deployment/coredns"]
