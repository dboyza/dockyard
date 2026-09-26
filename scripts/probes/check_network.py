"""Prove CNI policy enforcement against live TCP traffic in the probe cluster."""

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KUBECTL = [
    str(ROOT / ".tools/bin/kubectl"),
    "--kubeconfig",
    str(ROOT / ".runtime/probe/kubeconfig"),
]


def kubectl(*args: str, payload: dict | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*KUBECTL, *args],
        input=json.dumps(payload) if payload else None,
        capture_output=True,
        text=True,
        timeout=15,
    )


ip = kubectl(
    "get", "pod", "server", "-n", "dockyard-proof", "-o", "jsonpath={.status.podIP}"
).stdout


def reachable() -> bool:
    result = kubectl(
        "exec",
        "-n",
        "dockyard-proof",
        "client",
        "--",
        "wget",
        "-T",
        "2",
        "-qO-",
        f"http://{ip}:8080",
    )
    return result.returncode == 0 and result.stdout.strip() == "dockyard-network-proof"


def expect(value: bool) -> None:
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        if reachable() == value:
            return
        time.sleep(0.5)
    raise AssertionError(f"Expected network reachability={value}")


expect(True)
policy = {
    "apiVersion": "networking.k8s.io/v1",
    "kind": "NetworkPolicy",
    "metadata": {"name": "proof", "namespace": "dockyard-proof"},
    "spec": {
        "podSelector": {"matchLabels": {"app": "server"}},
        "policyTypes": ["Ingress"],
        "ingress": [],
    },
}
result = kubectl("apply", "-f", "-", payload=policy)
assert result.returncode == 0, result.stderr
expect(False)
policy["spec"]["ingress"] = [
    {
        "from": [{"podSelector": {"matchLabels": {"app": "client"}}}],
        "ports": [{"port": 8080, "protocol": "TCP"}],
    }
]
result = kubectl("apply", "-f", "-", payload=policy)
assert result.returncode == 0, result.stderr
expect(True)
evidence = {
    "baseline": "allowed",
    "deny_policy": "blocked",
    "explicit_allow": "allowed",
    "server_ip": ip,
}
(ROOT / ".artifacts/network-policy-proof.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps(evidence))
