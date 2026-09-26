"""Small, credential-free resource maps derived only from actual runtime responses."""

from __future__ import annotations

import json
from typing import Any

from dockyard.models import LabObservation, ObservedLink, ObservedResource
from dockyard.runtimes.docker import DockerRuntime, RuntimeErrorBase
from dockyard.runtimes.kubernetes import KubernetesRuntime
from dockyard.store import timestamp


def observe(runtime: DockerRuntime | KubernetesRuntime) -> LabObservation:
    snapshot = LabObservation(
        lab_id=runtime.lab.id,
        runtime=runtime.lab.runtime,
        observed_at=timestamp(),
        status="observed",
        message="Read-only runtime observation. Assessment is a separate action.",
    )
    if isinstance(runtime, KubernetesRuntime):
        # Verify the recorded node identities as well as the private API credential boundary.
        nodes = [
            runtime.verify(entry)
            for entry in json.loads(runtime.lab.resources.get("kind_inventory", "[]"))
        ]
        if not nodes or not all(node and node["State"]["Running"] for node in nodes):
            raise RuntimeErrorBase("The owned cluster is stopped or a recorded node is missing.")
        response = runtime.kubectl(
            ["get", "deploy,rs,sts,ds,pod,svc,endpointslice,pvc,pv", "-A", "-o", "json"],
            output_limit=4_000_000,
        )
        if not response.ok or response.truncated:
            raise RuntimeErrorBase(
                "The cluster could not return a complete bounded resource observation."
            )
        items = json.loads(response.stdout)["items"]
        kubernetes_resources(snapshot, items)
    else:
        # Discover newly created learner resources without changing persisted lifecycle state.
        view = DockerRuntime(runtime.lab.model_copy(deep=True), runtime.env, lambda _: None)
        records = view.discover()
        resources = [(entry, view.verify(entry)) for entry in records]
        docker_resources(snapshot, [(entry, item) for entry, item in resources if item])
    snapshot.observed_at = timestamp()
    return snapshot


def kubernetes_resources(snapshot: LabObservation, items: list[dict[str, Any]]) -> None:
    excluded = {
        "kube-system",
        "kube-public",
        "kube-node-lease",
        "local-path-storage",
        "dockyard-observer",
        "metallb-system",
        "traefik",
    }
    resources = [item for item in items if item["metadata"].get("namespace", "") not in excluded]
    claims = {
        (item["metadata"]["namespace"], item["metadata"]["name"]): item["metadata"]["uid"]
        for item in resources
        if item["kind"] == "PersistentVolumeClaim"
    }
    services = {
        (item["metadata"]["namespace"], item["metadata"]["name"]): item["metadata"]["uid"]
        for item in resources
        if item["kind"] == "Service"
    }
    volumes = {
        item["metadata"]["name"]: item["metadata"]["uid"]
        for item in resources
        if item["kind"] == "PersistentVolume"
    }
    if len(resources) > 500:
        raise RuntimeErrorBase(
            "This resource map exceeds 500 objects. "
            "Use the scoped terminal to inspect the larger environment."
        )
    for item in resources:
        metadata, kind = item["metadata"], item["kind"]
        uid, name, namespace = metadata["uid"], metadata["name"], metadata.get("namespace", "")
        spec, status = item.get("spec", {}), item.get("status", {})
        if kind == "EndpointSlice":
            service = services.get(
                (namespace, metadata.get("labels", {}).get("kubernetes.io/service-name", ""))
            )
            if service:
                for endpoint in item.get("endpoints") or []:
                    target = endpoint.get("targetRef", {}).get("uid")
                    if target:
                        snapshot.links.append(
                            ObservedLink(
                                source=service,
                                target=target,
                                relation=(
                                    "ready endpoint"
                                    if endpoint.get("conditions", {}).get("ready") is True
                                    else "unready endpoint"
                                    if endpoint.get("conditions", {}).get("ready") is False
                                    else "endpoint readiness unknown"
                                ),
                            )
                        )
            continue
        if kind == "ReplicaSet" and not spec.get("replicas", 0) and not status.get("replicas", 0):
            continue
        state = "Present"
        summary = ""
        if kind == "Pod":
            ready = any(
                c["type"] == "Ready" and c["status"] == "True" for c in status.get("conditions", [])
            )
            state = (
                "Terminating"
                if metadata.get("deletionTimestamp")
                else "Ready"
                if ready
                else "Not ready"
                if status.get("phase") == "Running"
                else status.get("phase", "Unknown")
            )
            restarts = sum(c.get("restartCount", 0) for c in status.get("containerStatuses", []))
            summary = f"{spec.get('nodeName', 'Not scheduled')} · {restarts} restarts"
            for volume in spec.get("volumes", []):
                target = claims.get(
                    (namespace, volume.get("persistentVolumeClaim", {}).get("claimName", ""))
                )
                if target:
                    snapshot.links.append(
                        ObservedLink(source=uid, target=target, relation="mounts claim")
                    )
        elif kind in {"Deployment", "ReplicaSet", "StatefulSet", "DaemonSet"}:
            desired = (
                status.get("desiredNumberScheduled", 0)
                if kind == "DaemonSet"
                else spec.get("replicas", 1)
            )
            ready = (
                status.get("numberReady", 0)
                if kind == "DaemonSet"
                else status.get("readyReplicas", 0)
            )
            state = (
                "Ready"
                if desired > 0
                and ready == desired
                and status.get("observedGeneration") == metadata.get("generation")
                else "Scaled to zero"
                if desired == 0
                else "Converging"
            )
            summary = f"{ready} ready / {desired} desired"
        elif kind == "Service":
            state = spec.get("type", "ClusterIP")
            summary = ", ".join(
                f"{p.get('port')} → {p.get('targetPort')}" for p in spec.get("ports", [])
            )
        elif kind == "PersistentVolumeClaim":
            state = status.get("phase", "Pending")
            size = spec.get("resources", {}).get("requests", {}).get("storage", "Unspecified size")
            summary = f"{spec.get('storageClassName', 'No class')} · {size}"
            target = volumes.get(spec.get("volumeName", ""))
            if target:
                snapshot.links.append(
                    ObservedLink(source=uid, target=target, relation="bound to volume")
                )
        elif kind == "PersistentVolume":
            claim = spec.get("claimRef", {})
            if (claim.get("namespace"), claim.get("name")) not in claims:
                continue
            state = status.get("phase", "Unknown")
            policy = spec.get("persistentVolumeReclaimPolicy", "Unknown policy")
            summary = f"{policy} · {spec.get('capacity', {}).get('storage', '')}"
        snapshot.resources.append(
            ObservedResource(
                id=uid, kind=kind, name=name, namespace=namespace, state=state, summary=summary
            )
        )
        for owner in metadata.get("ownerReferences", []):
            snapshot.links.append(ObservedLink(source=owner["uid"], target=uid, relation="owns"))
    known = {node.id for node in snapshot.resources}
    snapshot.links = [
        link for link in snapshot.links if link.source in known and link.target in known
    ]


def docker_resources(
    snapshot: LabObservation, items: list[tuple[dict[str, str], dict[str, Any]]]
) -> None:
    networks = {item["Name"]: entry["id"] for entry, item in items if entry["kind"] == "network"}
    volumes = {item["Name"]: entry["id"] for entry, item in items if entry["kind"] == "volume"}
    for entry, item in items:
        kind, identity = entry["kind"], entry["id"]
        state, summary = "Present", ""
        if kind == "container":
            state = item["State"]["Status"]
            summary = f"{item['Config']['Image']} · {item.get('RestartCount', 0)} restarts"
            for network in item.get("NetworkSettings", {}).get("Networks", {}):
                if network in networks:
                    snapshot.links.append(
                        ObservedLink(
                            source=identity, target=networks[network], relation="connected to"
                        )
                    )
            for mount in item.get("Mounts", []):
                if mount.get("Name") in volumes:
                    snapshot.links.append(
                        ObservedLink(
                            source=identity,
                            target=volumes[mount["Name"]],
                            relation=f"mounts at {mount['Destination']}",
                        )
                    )
        elif kind == "network":
            summary = f"{item.get('Driver', '')} network"
        elif kind == "volume":
            summary = f"{item.get('Driver', '')} volume"
        snapshot.resources.append(
            ObservedResource(
                id=identity,
                kind=kind.capitalize(),
                name=item["Name"].lstrip("/"),
                state=state,
                summary=summary,
            )
        )
