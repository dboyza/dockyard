"""Actual authorization, network enforcement, admission, and process restrictions."""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from contextlib import suppress
from typing import Any

from dockyard.probes.kubernetes import available, get, kubectl, owned_pods, sql
from dockyard.process import run


def execute(deployment: str, script: str, namespace: str = "dispatch") -> Any:
    return json.loads(
        kubectl(
            "exec",
            "-n",
            namespace,
            "deployment/" + deployment,
            "--",
            "python",
            "-c",
            script,
            timeout=25,
        )
    )


def request(path: str, payload: dict[str, Any] | None = None, method: str = "GET") -> Any:
    return execute(
        "trusted-client",
        "import json,urllib.request; "
        f"r=urllib.request.Request({'http://dispatch.dispatch.svc.cluster.local:8080' + path!r},"
        f"data={repr(json.dumps(payload).encode()) if payload is not None else 'None'},"
        f"headers={{'Content-Type':'application/json'}},method={method!r}); "
        "print(urllib.request.urlopen(r,timeout=3).read().decode())",
        "frontend",
    )


def connections(deployment: str, namespace: str, targets: list[tuple[str, int]]) -> list[bool]:
    script = f"""import json,socket
results=[]
for host,port in {targets!r}:
    try:
        with socket.create_connection((host,port),timeout=1.5): results.append(True)
    except OSError: results.append(False)
print(json.dumps(results))
"""
    return list(execute(deployment, script, namespace))


def security() -> dict[str, Any]:
    result: dict[str, Any] = dict.fromkeys(
        ("rbac", "tokens", "network", "dns", "admission", "runtime", "workflow"), False
    )
    details: dict[str, Any] = {}
    result["_details"] = details
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        authorization = execute(
            "inventory",
            """import json, ssl, urllib.request, urllib.error
from pathlib import Path

base = Path("/var/run/secrets/kubernetes.io/serviceaccount")
context = ssl.create_default_context(cafile=str(base / "ca.crt"))
headers = {"Authorization": "Bearer " + (base / "token").read_text()}
results = {}
for name, path in [
    ("pods", "/api/v1/namespaces/dispatch/pods"),
    ("secrets", "/api/v1/namespaces/dispatch/secrets"),
    ("other_namespace", "/api/v1/namespaces/kube-system/pods"),
]:
    request = urllib.request.Request(
        "https://kubernetes.default.svc" + path, headers=headers
    )
    try:
        with urllib.request.urlopen(request, context=context, timeout=3) as response:
            results[name] = response.status
    except urllib.error.HTTPError as error:
        results[name] = error.code
        error.close()
print(json.dumps(results))
""",
        )
        details["rbac"] = authorization
        identity = "system:serviceaccount:dispatch:dispatch-reader"
        permissions = [
            run(["kubectl", "auth", "can-i", verb, resource, "--as", identity]).stdout.strip()
            for verb, resource in (
                ("create", "pods"),
                ("patch", "deployments"),
                ("create", "rolebindings"),
            )
        ]
        result["rbac"] = (
            authorization == {"pods": 200, "secrets": 403, "other_namespace": 403}
            and permissions == ["no"] * 3
        )
        tokens = [
            execute(
                name,
                "from pathlib import Path; import json; "
                "print(json.dumps(Path('/var/run/secrets/kubernetes.io/'"
                "'serviceaccount/token').exists()))",
            )
            for name in ("dispatch", "worker")
        ]
        result["tokens"] = tokens == [False, False]
    with suppress(RuntimeError, ValueError, KeyError, OSError, IndexError):
        api = get("svc", "dispatch")["spec"]["clusterIP"]
        db = get("svc", "db")["spec"]["clusterIP"]
        queue = get("svc", "queue")["spec"]["clusterIP"]
        trap = get("svc", "egress-target", "dockyard-observer")["spec"]["clusterIP"]
        measured = {
            "trusted_frontend": connections(
                "trusted-client", "frontend", [(api, 8080), (db, 5432), (trap, 8080)]
            ),
            "untrusted_frontend": connections("untrusted-client", "frontend", [(api, 8080)]),
            "wrong_namespace": connections("outside-client", "dockyard-observer", [(api, 8080)]),
            "api_egress": connections(
                "dispatch", "dispatch", [(db, 5432), (queue, 6379), (trap, 8080)]
            ),
            "worker_egress": connections("worker", "dispatch", [(db, 5432), (queue, 6379)]),
        }
        _, api_pods = owned_pods("dispatch")
        _, clients = owned_pods("trusted-client", "frontend")
        different_nodes = all(
            p["spec"]["nodeName"] != clients[0]["spec"]["nodeName"] for p in api_pods
        )
        details["network"] = {**measured, "cross_node": different_nodes}
        result["network"] = different_nodes and measured == {
            "trusted_frontend": [True, False, True],
            "untrusted_frontend": [False],
            "wrong_namespace": [False],
            "api_egress": [True, True, False],
            "worker_egress": [True, True],
        }
        dns = execute(
            "dispatch",
            """import json, socket, struct
from pathlib import Path

server = next(
    line.split()[1]
    for line in Path("/etc/resolv.conf").read_text().splitlines()
    if line.startswith("nameserver")
)
name = "db.dispatch.svc.cluster.local"
query = (
    struct.pack("!HHHHHH", 0xD04C, 0x0100, 1, 0, 0, 0)
    + b"".join(bytes([len(x)]) + x.encode() for x in name.split("."))
    + b"\\0"
    + struct.pack("!HH", 1, 1)
)
results = {}
def read_exact(client, size):
    result = b""
    while len(result) < size:
        block = client.recv(size - len(result))
        if not block:
            raise OSError("DNS stream ended before its declared response")
        result += block
    return result

for protocol in ("udp", "tcp"):
    try:
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM if protocol == "udp" else socket.SOCK_STREAM,
        ) as client:
            client.settimeout(2)
            client.connect((server, 53))
            client.sendall(
                query if protocol == "udp" else struct.pack("!H", len(query)) + query
            )
            if protocol == "tcp":
                size = struct.unpack("!H", read_exact(client, 2))[0]
                if not 12 <= size <= 4096:
                    raise OSError("Unexpected DNS response size")
                response = read_exact(client, size)
            else:
                response = client.recv(4096)
            identity, flags, questions, answers, _, _ = struct.unpack(
                "!HHHHHH", response[:12]
            )
            results[protocol] = identity == 0xD04C and flags & 15 == 0 and answers > 0
    except (OSError, struct.error):
        results[protocol] = False
print(json.dumps(results))
""",
        )
        result["dns"] = dns == {"udp": True, "tcp": True}
        details["dns"] = dns
    with suppress(RuntimeError, ValueError, KeyError, OSError, IndexError):
        labels = get("namespace", "dispatch")["metadata"].get("labels", {})
        pod: dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "admission-observation", "namespace": "dispatch"},
            "spec": {
                "restartPolicy": "Never",
                "automountServiceAccountToken": False,
                "securityContext": {
                    "runAsNonRoot": True,
                    "runAsUser": 10001,
                    "seccompProfile": {"type": "RuntimeDefault"},
                },
                "containers": [
                    {
                        "name": "client",
                        "image": os.environ["DOCKYARD_IMAGE"],
                        "securityContext": {
                            "allowPrivilegeEscalation": False,
                            "capabilities": {"drop": ["ALL"]},
                        },
                    }
                ],
            },
        }
        valid = run(
            ["kubectl", "create", "--dry-run=server", "-f", "-"], input_text=json.dumps(pod)
        )
        pod["spec"]["containers"][0]["securityContext"]["allowPrivilegeEscalation"] = True
        rejected = run(
            ["kubectl", "create", "--dry-run=server", "-f", "-"], input_text=json.dumps(pod)
        )
        result["admission"] = (
            labels.get("pod-security.kubernetes.io/enforce") == "restricted"
            and labels.get("pod-security.kubernetes.io/enforce-version") == "v1.35"
            and valid.ok
            and not rejected.ok
            and "violates PodSecurity" in rejected.stderr
        )
        details["admission"] = {
            "enforce": labels.get("pod-security.kubernetes.io/enforce"),
            "valid_pod_accepted": valid.ok,
            "escalation_rejected": not rejected.ok,
        }
        observed = execute(
            "dispatch",
            """import json, os
from pathlib import Path

status = dict(
    line.split(":", 1)
    for line in Path("/proc/self/status").read_text().splitlines()
    if ":" in line
)
root = next(
    line.split()[3].split(",")
    for line in Path("/proc/mounts").read_text().splitlines()
    if line.split()[1] == "/"
)
print(
    json.dumps(
        {
            "uid": os.getuid(),
            "capabilities": int(status["CapEff"].strip(), 16),
            "no_new_privileges": int(status["NoNewPrivs"]),
            "seccomp": int(status["Seccomp"]),
            "root_readonly": "ro" in root,
        }
    )
)
""",
        )
        deployment, pods = owned_pods("dispatch")
        context = deployment["spec"]["template"]["spec"]["containers"][0].get("securityContext", {})
        result["runtime"] = (
            observed["uid"] != 0
            and observed["capabilities"] == 0
            and observed["no_new_privileges"] == 1
            and observed["seccomp"] == 2
            and observed["root_readonly"]
            and available(deployment, 2)
            and len(pods) == 2
            and context.get("allowPrivilegeEscalation") is False
        )
        details["runtime"] = observed
    job_id = None
    with suppress(RuntimeError, ValueError, KeyError, OSError):
        try:
            title = "restricted-" + uuid.uuid4().hex
            job_id = request("/jobs", {"title": title}, "POST")["id"]
            if (
                not isinstance(job_id, str)
                or len(job_id) != 32
                or any(c not in "0123456789abcdef" for c in job_id)
            ):
                raise ValueError("Invalid observed job ID")
            _, workers = owned_pods("worker")
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                row = json.loads(
                    sql(
                        f"SELECT row_to_json(j) FROM jobs j WHERE id='{job_id}'",
                        workload="statefulset/db",
                    )
                )
                if row["status"] == "done":
                    result["workflow"] = (
                        row["title"] == title
                        and row["result"]
                        == {
                            "normalized": title.upper(),
                            "sha256": hashlib.sha256(title.encode()).hexdigest(),
                        }
                        and row["worker"] in {p["metadata"]["name"] for p in workers}
                    )
                    break
                time.sleep(0.3)
        finally:
            if (
                isinstance(job_id, str)
                and len(job_id) == 32
                and all(c in "0123456789abcdef" for c in job_id)
            ):
                sql(f"DELETE FROM jobs WHERE id='{job_id}'", workload="statefulset/db")
    return result
