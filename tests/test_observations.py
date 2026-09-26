"""Resource maps expose bounded relationships without workload credentials or configuration."""

from dockyard.models import LabObservation, Runtime
from dockyard.observations import docker_resources, kubernetes_resources


def snapshot(runtime=Runtime.KUBERNETES):
    return LabObservation(
        lab_id="test", runtime=runtime, observed_at="now", status="observed", message="test"
    )


def resource(kind, name, uid, spec=None, status=None, **metadata):
    return {
        "kind": kind,
        "metadata": {"name": name, "uid": uid, "namespace": "dispatch", **metadata},
        "spec": spec or {},
        "status": status or {},
    }


def test_kubernetes_relationships_follow_uids_and_actual_endpoint_readiness():
    observed = snapshot()
    service = resource("Service", "api", "service", {"ports": [{"port": 80, "targetPort": 8080}]})
    controller = resource(
        "Deployment",
        "api",
        "controller",
        {"replicas": 1},
        {"readyReplicas": 1, "observedGeneration": 2},
        generation=2,
    )
    pod = resource(
        "Pod",
        "api-123",
        "pod",
        {
            "containers": [{"env": [{"name": "PASSWORD", "value": "never-display"}]}],
            "volumes": [{"persistentVolumeClaim": {"claimName": "data"}}],
        },
        {"phase": "Running", "conditions": [{"type": "Ready", "status": "False"}]},
        ownerReferences=[{"uid": "controller"}],
    )
    claim = resource(
        "PersistentVolumeClaim", "data", "claim", {"volumeName": "volume"}, {"phase": "Bound"}
    )
    volume = resource(
        "PersistentVolume",
        "volume",
        "volume",
        {
            "claimRef": {"namespace": "dispatch", "name": "data"},
            "hostPath": {"path": "/private/host/path"},
        },
        {"phase": "Bound"},
    )
    endpoints = resource(
        "EndpointSlice", "api-abc", "slice", labels={"kubernetes.io/service-name": "api"}
    )
    endpoints["endpoints"] = [{"targetRef": {"uid": "pod"}, "conditions": {"ready": False}}]
    system = resource("Pod", "system", "system", namespace="kube-system")
    kubernetes_resources(observed, [service, controller, pod, claim, volume, endpoints, system])
    assert {r.id for r in observed.resources} == {"service", "controller", "pod", "claim", "volume"}
    assert {(link.source, link.target, link.relation) for link in observed.links} == {
        ("service", "pod", "unready endpoint"),
        ("controller", "pod", "owns"),
        ("pod", "claim", "mounts claim"),
        ("claim", "volume", "bound to volume"),
    }
    assert "never-display" not in observed.model_dump_json()
    assert "/private/host/path" not in observed.model_dump_json()
    assert next(r for r in observed.resources if r.id == "pod").state == "Not ready"


def test_docker_map_uses_only_verified_inventory_and_omits_environment():
    observed = snapshot(Runtime.DOCKER)
    docker_resources(
        observed,
        [
            ({"kind": "network", "id": "network"}, {"Name": "owned-net", "Driver": "bridge"}),
            ({"kind": "volume", "id": "volume"}, {"Name": "owned-data", "Driver": "local"}),
            (
                {"kind": "container", "id": "container"},
                {
                    "Name": "/api",
                    "State": {"Status": "running"},
                    "Config": {"Image": "app:practice", "Env": ["PASSWORD=private"]},
                    "NetworkSettings": {"Networks": {"owned-net": {}, "unrelated": {}}},
                    "Mounts": [{"Name": "owned-data", "Destination": "/data"}],
                },
            ),
        ],
    )
    assert len(observed.resources) == 3
    assert len(observed.links) == 2
    assert "PASSWORD" not in observed.model_dump_json()
    assert "unrelated" not in observed.model_dump_json()


def test_empty_endpoint_slice_is_an_observed_service_without_traffic_edges():
    observed = snapshot()
    service = resource("Service", "api", "service")
    endpoints = resource(
        "EndpointSlice", "empty", "slice", labels={"kubernetes.io/service-name": "api"}
    )
    endpoints["endpoints"] = None
    kubernetes_resources(observed, [service, endpoints])
    assert [item.id for item in observed.resources] == ["service"]
    assert observed.links == []
