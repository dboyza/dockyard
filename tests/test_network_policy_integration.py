"""The practice cluster's network plugin enforces NetworkPolicy, on one node and across two.

Rerun this whenever the kind pin changes: the lessons trust kind's own plugin to enforce.
"""

import os
import time

import pytest
import yaml

from dockyard.process import run
from dockyard.service import Service

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("DOCKYARD_INTEGRATION") != "1", reason="opt-in real Kubernetes"
    ),
]
NAMESPACE = "policy-proof"


def test_policies_isolate_allow_by_label_and_survive_a_restart(lab_profile):
    service = Service(lab_profile)
    unit_id = "m17-network"
    service.perform(unit_id, "prepare")
    lab = service.store.lab(unit_id)
    assert lab is not None
    env = service.environment(lab)
    image = env["DOCKYARD_BUSYBOX_LOCAL_IMAGE"]

    def kubectl(*args, payload=None):
        return run(["kubectl", *args], env=env, timeout=120, input_text=payload)

    nodes = kubectl("get", "nodes", "-o", "jsonpath={.items[*].metadata.name}").stdout.split()
    worker = next(name for name in nodes if "worker" in name)
    control = next(name for name in nodes if name.endswith("control-plane"))

    def pod(name, node):
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": name, "namespace": NAMESPACE, "labels": {"app": name}},
            "spec": {
                "nodeSelector": {"kubernetes.io/hostname": node},
                "tolerations": [{"operator": "Exists"}],
                "containers": [
                    {
                        "name": "main",
                        "image": image,
                        "imagePullPolicy": "Never",
                        "command": [
                            "sh",
                            "-c",
                            "mkdir -p /www && echo ok > /www/index.html "
                            "&& httpd -f -p 8080 -h /www",
                        ],
                        "ports": [{"name": "web", "containerPort": 8080}],
                    }
                ],
            },
        }

    def policy(name, spec):
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": name, "namespace": NAMESPACE},
            "spec": spec,
        }

    def apply(*documents):
        assert kubectl("apply", "-f", "-", payload=yaml.safe_dump_all(documents)).ok

    def reaches(source, address):
        return kubectl("-n", NAMESPACE, "exec", source, "--", "wget", "-T", "2", "-qO-", address).ok

    def settles(source, address, expected):
        # Policies take effect within seconds; give the plugin a bounded moment.
        deadline = time.monotonic() + 30
        while reaches(source, address) != expected:
            if time.monotonic() > deadline:
                return False
            time.sleep(1)
        return True

    assert kubectl("create", "namespace", NAMESPACE).ok
    # The server is on the worker; one client shares its node and two do not.
    apply(pod("server", worker), pod("near", worker), pod("client", control), pod("other", control))
    assert kubectl("-n", NAMESPACE, "wait", "--for=condition=Ready", "pod", "--all").ok
    address = kubectl(
        "-n", NAMESPACE, "get", "pod", "server", "-o", "jsonpath={.status.podIP}"
    ).stdout
    target = f"http://{address}:8080/"
    for source in ("client", "near"):
        assert settles(source, target, True), f"{source} never reached the server"

    apply(policy("deny", {"podSelector": {}, "policyTypes": ["Ingress"]}))
    assert settles("client", target, False), "a cross-node request passed a default deny"
    assert settles("near", target, False), "a same-node request passed a default deny"

    apply(
        policy(
            "allow-client",
            {
                "podSelector": {"matchLabels": {"app": "server"}},
                "ingress": [
                    {
                        "from": [{"podSelector": {"matchLabels": {"app": "client"}}}],
                        "ports": [{"port": "web"}],
                    }
                ],
            },
        )
    )
    assert settles("client", target, True), "an allowed client was still refused"
    assert not reaches("other", target) and not reaches("near", target)

    service.perform(unit_id, "stop")
    service.perform(unit_id, "resume")
    assert kubectl("-n", NAMESPACE, "wait", "--for=condition=Ready", "pod", "--all").ok
    address = kubectl(
        "-n", NAMESPACE, "get", "pod", "server", "-o", "jsonpath={.status.podIP}"
    ).stdout
    target = f"http://{address}:8080/"
    assert settles("client", target, True), "the allowed client lost access after a restart"
    assert not reaches("other", target), "the policy stopped isolating after a restart"
