"""Observe initialized native clusters, joined networking, and actual HA quorum."""

from __future__ import annotations

import json
import sys
import uuid
from contextlib import suppress
from typing import Any

import yaml

from dockyard.native import current
from dockyard.probes.native import workflow
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.runtimes.native_cluster import POD_CIDR

ERRORS = (RuntimeError, ValueError, KeyError, OSError, IndexError, StopIteration, TypeError)


def containers(runtime: LinuxRuntime, name: str) -> list[dict[str, Any]]:
    result = runtime.guest(name, ["sudo", "crictl", "ps", "-o", "json"], timeout=20)
    runtime.require(result)
    return list(json.loads(result.stdout)["containers"])


def bootstrap() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(("initialized", "network", "workflow"), False)
    details: dict[str, Any] = {}
    result["_details"] = details
    runtime = current()
    names = [entry["name"] for entry in runtime.discover()]
    with suppress(*ERRORS):
        observed = runtime.guest(
            names[0],
            [
                "sudo",
                "kubectl",
                "--kubeconfig=/etc/kubernetes/admin.conf",
                "--request-timeout=5s",
                "get",
                "--raw=/readyz",
            ],
            timeout=15,
        )
        configured = runtime.guest(
            names[0],
            [
                "sudo",
                "kubectl",
                "--kubeconfig=/etc/kubernetes/admin.conf",
                "--request-timeout=5s",
                "get",
                "configmap",
                "kubeadm-config",
                "-n",
                "kube-system",
                "-o",
                "json",
            ],
            timeout=15,
        )
        config = yaml.safe_load(json.loads(configured.stdout)["data"]["ClusterConfiguration"])
        running = {
            item.get("labels", {}).get("io.kubernetes.container.name")
            for item in containers(runtime, names[0])
        }
        required = {"etcd", "kube-apiserver", "kube-controller-manager", "kube-scheduler"}
        client = runtime.kubectl(["get", "--raw=/version"], timeout=15)
        actual_version = json.loads(client.stdout)["gitVersion"]
        result["initialized"] = bool(
            client.ok
            and actual_version == "v1.35.8"
            and observed.ok
            and observed.stdout.strip() == "ok"
            and required <= running
            and config["networking"]["podSubnet"] == POD_CIDR
        )
        details["initialized"] = {
            "api_ready": observed.ok,
            "private_client_server_version": actual_version,
            "running_static_components": sorted(required & running),
            "pod_subnet": config["networking"]["podSubnet"],
        }
    with suppress(*ERRORS):
        observed = runtime.kubectl(["get", "nodes", "-o", "json"], timeout=15)
        runtime.require(observed)
        nodes = json.loads(observed.stdout)["items"]
        ready = {
            node["metadata"]["name"]
            for node in nodes
            if any(
                condition["type"] == "Ready" and condition["status"] == "True"
                for condition in node.get("status", {}).get("conditions", [])
            )
        }
        cni = runtime.kubectl(
            ["get", "daemonset", "calico-node", "-n", "kube-system", "-o", "json"], timeout=15
        )
        dns = runtime.kubectl(
            ["get", "deployment", "coredns", "-n", "kube-system", "-o", "json"], timeout=15
        )
        cni_status = json.loads(cni.stdout)["status"]
        dns_status = json.loads(dns.stdout)["status"]
        result["network"] = bool(
            ready == {"lima-" + name for name in names}
            and cni_status.get("numberReady") == len(names)
            and dns_status.get("availableReplicas", 0) >= 1
        )
        details["network"] = {
            "ready_nodes": sorted(ready),
            "ready_cni_agents": cni_status.get("numberReady", 0),
            "available_dns_replicas": dns_status.get("availableReplicas", 0),
        }
    with suppress(*ERRORS):
        result["workflow"] = workflow()
    return result


def high_availability() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(("outage", "quorum", "endpoint", "workflow"), False)
    details: dict[str, Any] = {}
    result["_details"] = details
    runtime = current()
    names = [entry["name"] for entry in runtime.discover()]
    if len(names) != 4:
        return result
    with suppress(*ERRORS):
        primary = {
            item.get("labels", {}).get("io.kubernetes.container.name")
            for item in containers(runtime, names[0])
        }
        result["outage"] = not bool(primary & {"etcd", "kube-apiserver"})
        details["outage"] = {
            "primary_api_running": "kube-apiserver" in primary,
            "primary_etcd_running": "etcd" in primary,
        }
    with suppress(*ERRORS):
        health = {}
        for name in names[1:-1]:
            container = next(
                item["id"]
                for item in containers(runtime, name)
                if item.get("labels", {}).get("io.kubernetes.container.name") == "etcd"
            )
            command = [
                "sudo",
                "crictl",
                "exec",
                container,
                "etcdctl",
                "--endpoints=https://127.0.0.1:2379",
                "--cacert=/etc/kubernetes/pki/etcd/ca.crt",
                "--cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt",
                "--key=/etc/kubernetes/pki/etcd/healthcheck-client.key",
            ]
            observed = runtime.guest(
                name, command + ["endpoint", "health", "-w", "json"], timeout=20
            )
            membership = runtime.guest(name, command + ["member", "list", "-w", "json"], timeout=20)
            members = json.loads(membership.stdout)["members"]
            expected = {"lima-" + entry for entry in names[:-1]}
            health[name] = bool(
                observed.ok
                and json.loads(observed.stdout)[0]["health"] is True
                and membership.ok
                and {member["name"] for member in members} == expected
                and all(not member.get("isLearner", False) for member in members)
            )
        result["quorum"] = all(health.values()) and len(health) == 2
        details["quorum"] = {"healthy_voting_endpoints": health, "expected_voters": 3}
    name = "dockyard-ha-" + uuid.uuid4().hex[:12]
    created = False
    try:
        with suppress(*ERRORS):
            observed = runtime.kubectl(
                ["create", "configmap", name, "--from-literal=quorum=survived", "-n", "default"],
                timeout=15,
            )
            created = observed.ok
            if created:
                observed = runtime.kubectl(
                    ["get", "configmap", name, "-n", "default", "-o", "json"], timeout=15
                )
                result["endpoint"] = bool(
                    observed.ok and json.loads(observed.stdout)["data"]["quorum"] == "survived"
                )
            details["endpoint"] = {"fresh_api_write_and_read": result["endpoint"]}
    finally:
        if created:
            deleted = runtime.kubectl(
                ["delete", "configmap", name, "-n", "default", "--wait=false"], timeout=15
            )
            result["endpoint"] = result["endpoint"] and deleted.ok
    with suppress(*ERRORS):
        result["workflow"] = workflow()
    return result


if __name__ == "__main__":
    print(json.dumps(high_availability() if sys.argv[1:] == ["ha"] else bootstrap()))
