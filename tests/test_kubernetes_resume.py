from dockyard.runtimes.kubernetes import parse_time, stale_pods

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


def test_calico_pool_is_set_in_the_cached_manifest():
    from pathlib import Path

    import pytest

    from dockyard.runtimes.kubernetes import calico_pool

    cached = Path(".tools/downloads/calico-v3.32.2.yaml")
    if not cached.exists():
        pytest.skip("The Calico manifest is downloaded by the toolchain.")
    manifest = calico_pool(cached.read_text(), "10.244.0.0/16")
    assert '- name: CALICO_IPV4POOL_CIDR\n              value: "10.244.0.0/16"' in manifest
    assert '#   value: "192.168.0.0/16"' not in manifest
