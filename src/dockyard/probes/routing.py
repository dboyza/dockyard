"""Verify routing with real clients, controller conditions, and owned endpoints."""

from __future__ import annotations

import ipaddress
import json
import os
import uuid
from contextlib import suppress
from typing import Any

from dockyard.probes.kubernetes import api_request, get, owned_pods
from dockyard.process import run


def condition(resource: dict[str, Any], kind: str) -> bool:
    return any(
        item.get("type") == kind
        and item.get("status") == "True"
        and item.get("observedGeneration") == resource["metadata"]["generation"]
        for item in resource.get("status", {}).get("conditions", [])
    )


def routing() -> dict[str, bool]:
    result = dict.fromkeys(
        ("service", "endpoints", "nodeport", "loadbalancer", "tls", "gateway", "host_boundary"),
        False,
    )
    _, pods = owned_pods("dispatch")
    names = {pod["metadata"]["name"] for pod in pods}

    def response(args: list[str], timeout: float = 10) -> bool:
        observed = run(args, timeout=timeout)
        if not observed.ok:
            return False
        with suppress(ValueError, KeyError, TypeError):
            body = json.loads(observed.stdout)
            return bool(body.get("service") == "dispatch" and body.get("hostname") in names)
        return False

    with suppress(RuntimeError, ValueError, KeyError):
        body = api_request("/healthz")
        result["service"] = body.get("service") == "dispatch" and body.get("hostname") in names
    with suppress(RuntimeError, ValueError, KeyError):
        slices = get("endpointslices")["items"]
        endpoints = [
            endpoint
            for item in slices
            if item["metadata"].get("labels", {}).get("kubernetes.io/service-name") == "dispatch"
            for endpoint in item.get("endpoints", [])
            if endpoint.get("conditions", {}).get("ready") is True
        ]
        expected = {pod["metadata"]["uid"]: pod["status"]["podIP"] for pod in pods}
        result["endpoints"] = (
            len(expected) == 2
            and {e.get("targetRef", {}).get("uid"): e["addresses"][0] for e in endpoints}
            == expected
        )
    curl = ["curl", "--noproxy", "*", "--silent", "--show-error", "--max-time", "4"]
    http = f"http://127.0.0.1:{os.environ['DOCKYARD_PORT']}/healthz"
    result["nodeport"] = response([*curl, "--fail", http])
    with suppress(RuntimeError, ValueError, KeyError, IndexError):
        service = get("service", "dispatch-public")
        address = service["status"]["loadBalancer"]["ingress"][0]["ip"]
        pools = get("ipaddresspools.metallb.io", namespace="metallb-system")["items"]
        allocated = ipaddress.ip_address(address)
        valid = False
        for pool in pools:
            for entry in pool["spec"]["addresses"]:
                if "-" in entry:
                    start, end = entry.split("-", 1)
                    first, last = ipaddress.ip_address(start), ipaddress.ip_address(end)
                    valid |= first.version == allocated.version == last.version and int(
                        first
                    ) <= int(allocated) <= int(last)
                else:
                    valid |= allocated in ipaddress.ip_network(entry)
        result["loadbalancer"] = (
            service["spec"]["type"] == "LoadBalancer"
            and valid
            and response(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--name",
                    "dockyard-observe-" + uuid.uuid4().hex[:12],
                    "--label",
                    "io.dockyard.lab=" + os.environ["DOCKYARD_LAB"],
                    "--network",
                    os.environ["DOCKYARD_NETWORK"],
                    os.environ["DOCKYARD_BUSYBOX_IMAGE"],
                    "wget",
                    "-T",
                    "4",
                    "-qO-",
                    f"http://{address}:8080/healthz",
                ],
                timeout=12,
            )
        )
    port = os.environ["DOCKYARD_TLS_PORT"]
    result["tls"] = response(
        [
            *curl,
            "--fail",
            "--cacert",
            os.environ["DOCKYARD_TLS_CERT"],
            "--resolve",
            f"dispatch.test:{port}:127.0.0.1",
            f"https://dispatch.test:{port}/healthz",
        ]
    )
    with suppress(RuntimeError, ValueError, KeyError):
        gateway = get("gateways.gateway.networking.k8s.io", "dispatch-gateway")
        route = get("httproutes.gateway.networking.k8s.io", "dispatch")
        attached = any(
            parent.get("parentRef", {}).get("name") == "dispatch-gateway"
            and parent.get("controllerName") == "traefik.io/gateway-controller"
            and all(
                condition({"metadata": route["metadata"], "status": parent}, kind)
                for kind in ("Accepted", "ResolvedRefs")
            )
            for parent in route.get("status", {}).get("parents", [])
        )
        result["gateway"] = (
            attached
            and condition(gateway, "Programmed")
            and response([*curl, "--fail", "-H", "Host: gateway.dispatch.test", http])
        )
    unknown = run(
        [
            *curl,
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            "-H",
            "Host: unmatched.dispatch.test",
            http,
        ],
        timeout=8,
    )
    result["host_boundary"] = unknown.ok and unknown.stdout.strip() == "404"
    return result
