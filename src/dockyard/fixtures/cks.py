"""Security weaknesses each CKS lab starts from, applied only to that lab's own cluster."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from dockyard import host
from dockyard.catalog import CONTENT
from dockyard.fixtures.maintenance import record
from dockyard.native import current
from dockyard.probes.maintenance import observed
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.versions import KUBERNETES
from dockyard.workspace import atomic_write

STAGED = "/opt/dockyard/staged"
BINARIES = ("kubeadm", "kubelet", "kubectl")

# Weaken the worker kubelet the way an old provisioning script might have.
OPEN_KUBELET = """
from pathlib import Path
import yaml
path = Path('/var/lib/kubelet/config.yaml')
config = yaml.safe_load(path.read_text())
config['authentication']['anonymous']['enabled'] = True
config['authorization']['mode'] = 'AlwaysAllow'
path.write_text(yaml.safe_dump(config, sort_keys=False))
"""


# The kubelet's old read-only API serves Pod and node details without authentication.
READ_ONLY_PORT = """
from pathlib import Path
import yaml
path = Path('/var/lib/kubelet/config.yaml')
config = yaml.safe_load(path.read_text())
config['readOnlyPort'] = 10255
path.write_text(yaml.safe_dump(config, sort_keys=False))
"""


def wait_ready(r: LinuxRuntime, node: str, seconds: float = 120) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        status = observed(r, ["get", "node", node])["status"]["conditions"]
        if any(c["type"] == "Ready" and c["status"] == "True" for c in status):
            return
        time.sleep(2)
    raise RuntimeError(f"Node {node} did not return to Ready after its kubelet restarted.")


def reconfigure_kubelet(r: LinuxRuntime, guest: str, script: str) -> None:
    r.require(r.guest(guest, ["sudo", "python3", "-c", script]))
    r.require(r.guest(guest, ["sudo", "systemctl", "restart", "kubelet"]))
    # The kubelet reports Ready again once its new configuration is running.
    time.sleep(5)
    wait_ready(r, "lima-" + guest)


def open_kubelet(r: LinuxRuntime, guest: str) -> None:
    reconfigure_kubelet(r, guest, OPEN_KUBELET)


def open_read_only_port(r: LinuxRuntime, guest: str) -> None:
    reconfigure_kubelet(r, guest, READ_ONLY_PORT)


# A stand-in for a cloud provider's instance metadata service, which hands out node
# credentials to anything that asks from the node's network.
METADATA_UNIT = """[Unit]
Description=Dockyard practice instance metadata service
After=network-online.target

[Service]
ExecStartPre=/usr/sbin/ip address replace 169.254.169.254/32 dev lo
ExecStart=/usr/bin/python3 -m http.server 80 --bind 169.254.169.254 \\
  --directory /var/lib/dockyard/metadata
Restart=always

[Install]
WantedBy=multi-user.target
"""
CREDENTIAL = (
    '{"Code": "Success", "AccessKeyId": "DOCKYARD-PRACTICE-ONLY", '
    '"SecretAccessKey": "not-a-real-secret", "Note": "A practice stand-in for node credentials."}'
)
OPEN_EGRESS = """apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-egress
  namespace: frontend
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - {}
"""

# A first attempt that blocks only the metadata address and leaves the nodes open.
EXCEPT_METADATA = """apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-egress
  namespace: frontend
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
"""


def metadata_service(r: LinuxRuntime, guest: str) -> None:
    folder = "/var/lib/dockyard/metadata/latest/meta-data/iam/security-credentials"
    script = (
        f"mkdir -p {folder} && printf '%s' '{CREDENTIAL}' > {folder}/node-role && "
        "cat > /etc/systemd/system/dockyard-metadata.service && "
        "systemctl daemon-reload && systemctl enable --now dockyard-metadata"
    )
    r.require(r.guest(guest, ["sudo", "sh", "-c", script], input_text=METADATA_UNIT))
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        probe = r.guest(guest, ["curl", "-sf", "http://169.254.169.254/latest/meta-data/"])
        if probe.ok:
            return
        time.sleep(1)
    raise RuntimeError("The practice metadata service did not start on " + guest + ".")


def release_checksums() -> dict[str, str]:
    record = json.loads((CONTENT / "runtime/linux/release-checksums.json").read_text())
    if record["version"] != KUBERNETES:
        raise RuntimeError("The pinned release checksums do not match the cluster's version.")
    return dict(record["sha512"][host.architecture()])


def stage_binaries(r: LinuxRuntime, altered: str) -> None:
    """Stage the installed binaries for 'the next maintenance window', one altered."""
    copies = " && ".join(f"cp /usr/bin/{name} {STAGED}/{name}" for name in BINARIES)
    # Appended bytes leave the binary runnable and reporting its usual version.
    script = (
        f"rm -rf {STAGED} && mkdir -p {STAGED} && {copies} && "
        f"printf 'dockyard practice alteration' >> {STAGED}/{altered}"
    )
    r.require(r.guest(r.primary, ["sudo", "sh", "-c", script]))
    folder = Path("release-checksums")
    folder.mkdir(exist_ok=True)
    for name, value in release_checksums().items():
        atomic_write(folder / f"{name}.sha512", (value + "\n").encode())


# Someone once exposed status information to unauthenticated callers "for a dashboard".
PUBLIC_STATUS = """apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: status-reader
rules:
- apiGroups: [""]
  resources: ["pods", "configmaps"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: public-status
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: status-reader
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: system:unauthenticated
"""


# Access granted in a hurry: a CI identity with cluster-admin and a wildcard operators role.
BROAD_ACCESS = """apiVersion: v1
kind: Namespace
metadata:
  name: ci
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: deployer
  namespace: ci
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ci-deployer-admin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: deployer
  namespace: ci
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: dispatch-ops
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dispatch-operators-all
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dispatch-ops
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: dispatch-operators
"""


# Findings for the access review mission, each a variation on the module's lessons.
ACCESS_REVIEW = """apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: legacy-dashboard
  namespace: dispatch
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: User
  name: system:anonymous
---
apiVersion: v1
kind: Namespace
metadata:
  name: ci
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: deployer
  namespace: ci
---
apiVersion: v1
kind: Secret
metadata:
  name: deployer-token
  namespace: ci
  annotations:
    kubernetes.io/service-account.name: deployer
type: kubernetes.io/service-account-token
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: auditors-admin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: admin
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: auditors
"""


# Installed on the worker by an old package, where packaged services keep their unit files.
REPORT_SHARE = """[Unit]
Description=Report share for the old reporting server
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 -m http.server 8081 --bind 0.0.0.0 --directory /srv/report-share
Restart=always

[Install]
WantedBy=multi-user.target
"""
LEFTOVERS = (
    "mkdir -p /srv/report-share && "
    "printf 'node inventory for the old reporting server\\n' > /srv/report-share/inventory.txt && "
    "cat > /usr/lib/systemd/system/report-share.service && "
    "systemctl daemon-reload && systemctl enable --now report-share && "
    "(id backup >/dev/null 2>&1 || useradd --create-home --shell /bin/bash backup) && "
    "printf 'backup ALL=(ALL) NOPASSWD:ALL\\n' > /etc/sudoers.d/backup && "
    "chmod 440 /etc/sudoers.d/backup"
)


# A debugging share and a contractor account left on the control plane.
DEBUG_SHARE = REPORT_SHARE.replace(
    "Report share for the old reporting server", "Debug share"
).replace(
    "8081 --bind 0.0.0.0 --directory /srv/report-share", "2222 --bind 0.0.0.0 --directory /var/log"
)
CONTRACTOR = (
    "cat > /usr/lib/systemd/system/debug-share.service && "
    "systemctl daemon-reload && systemctl enable --now debug-share && "
    "(id contractor >/dev/null 2>&1 || useradd --create-home --shell /bin/bash contractor) && "
    "printf 'contractor ALL=(ALL) NOPASSWD:ALL\\n' > /etc/sudoers.d/contractor && "
    "chmod 440 /etc/sudoers.d/contractor"
)


# Something quietly reads the database password every twenty seconds; audit logs find it.
SECRET_READER = """apiVersion: v1
kind: Namespace
metadata:
  name: telemetry
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: metrics-exporter
  namespace: telemetry
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: read-database-secret
  namespace: dispatch
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["dispatch-database"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: metrics-exporter-secret
  namespace: dispatch
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: read-database-secret
subjects:
- kind: ServiceAccount
  name: metrics-exporter
  namespace: telemetry
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-exporter
  namespace: telemetry
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metrics-exporter
  template:
    metadata:
      labels:
        app: metrics-exporter
    spec:
      serviceAccountName: metrics-exporter
      containers:
      - name: exporter
        image: ${DOCKYARD_IMAGE}
        imagePullPolicy: Never
        command: ["python", "-c"]
        args:
        - |
          import ssl, time, urllib.request
          account = "/var/run/secrets/kubernetes.io/serviceaccount/"
          url = "https://kubernetes.default.svc/api/v1/namespaces/dispatch/secrets/dispatch-database"
          while True:
              try:
                  token = open(account + "token").read()
                  headers = {"Authorization": "Bearer " + token}
                  request = urllib.request.Request(url, headers=headers)
                  context = ssl.create_default_context(cafile=account + "ca.crt")
                  urllib.request.urlopen(request, context=context, timeout=5).read()
                  print("exported metrics", flush=True)
              except Exception as error:
                  reason = getattr(error, "reason", error)
                  print("export failed", type(error).__name__, reason, flush=True)
              time.sleep(20)
        resources:
          requests: {cpu: 10m, memory: 32Mi}
          limits: {cpu: 100m, memory: 96Mi}
"""


# Falco is installed by the guest tool bundle; this unit lets the learner run it as a service.
FALCO_UNIT = """[Unit]
Description=Falco runtime security
After=containerd.service

[Service]
ExecStart=/usr/bin/falco -o engine.kind=modern_ebpf
Restart=always

[Install]
WantedBy=multi-user.target
"""
SHELL_SPAWNER = """apiVersion: v1
kind: Namespace
metadata:
  name: billing
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: report-sync
  namespace: billing
spec:
  replicas: 1
  selector:
    matchLabels:
      app: report-sync
  template:
    metadata:
      labels:
        app: report-sync
    spec:
      automountServiceAccountToken: false
      nodeSelector:
        kubernetes.io/hostname: lima-${DOCKYARD_WORKER}
      containers:
      - name: sync
        image: ${DOCKYARD_IMAGE}
        imagePullPolicy: Never
        command: ["python", "-c"]
        args:
        - |
          import subprocess, time
          while True:
              subprocess.run(["sh", "-c", "id > /dev/null; uname -a > /dev/null"])
              print("synced", flush=True)
              time.sleep(15)
        resources:
          requests: {cpu: 10m, memory: 32Mi}
          limits: {cpu: 100m, memory: 96Mi}
"""


# A storefront workload behaving like a foothold: shells, Secret reads, metadata probes.
INTRUSION = """apiVersion: v1
kind: Namespace
metadata:
  name: storefront
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: catalog
  namespace: storefront
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: catalog-support
  namespace: dispatch
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: catalog-support
  namespace: dispatch
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: catalog-support
subjects:
- kind: ServiceAccount
  name: catalog
  namespace: storefront
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalog
  namespace: storefront
spec:
  replicas: 1
  selector:
    matchLabels:
      app: catalog
  template:
    metadata:
      labels:
        app: catalog
    spec:
      serviceAccountName: catalog
      nodeSelector:
        kubernetes.io/hostname: lima-${DOCKYARD_WORKER}
      containers:
      - name: catalog
        image: ${DOCKYARD_IMAGE}
        imagePullPolicy: Never
        command: ["python", "-c"]
        args:
        - |
          import socket, ssl, subprocess, time, urllib.request
          account = "/var/run/secrets/kubernetes.io/serviceaccount/"
          url = "https://kubernetes.default.svc/api/v1/namespaces/dispatch/secrets"
          while True:
              subprocess.run(["sh", "-c", "id > /dev/null"])
              try:
                  headers = {"Authorization": "Bearer " + open(account + "token").read()}
                  context = ssl.create_default_context(cafile=account + "ca.crt")
                  request = urllib.request.Request(url, headers=headers)
                  urllib.request.urlopen(request, context=context, timeout=5).read()
              except Exception:
                  pass
              try:
                  socket.create_connection(("169.254.169.254", 80), timeout=2).close()
              except OSError:
                  pass
              print("catalog refreshed", flush=True)
              time.sleep(20)
        resources:
          requests: {cpu: 10m, memory: 32Mi}
          limits: {cpu: 100m, memory: 96Mi}
"""


def install_falco_unit(r: LinuxRuntime) -> None:
    """Give the worker a systemd unit for the installed Falco, without starting it."""
    command = "cat > /etc/systemd/system/falco.service && systemctl daemon-reload"
    r.require(r.guest(r.worker, ["sudo", "sh", "-c", command], input_text=FALCO_UNIT))


def tamper(r: LinuxRuntime, namespace: str, selector: str) -> None:
    """Drop a program into one running replica, recording which one outside the workspace."""
    pods = observed(r, ["get", "pods", "-n", namespace, "-l", selector])["items"]
    running = sorted(
        pod["metadata"]["name"] for pod in pods if pod["status"].get("phase") == "Running"
    )
    if len(running) < 2:
        raise RuntimeError("The tampering scenario needs at least two running replicas.")
    # The middle replica, so neither the first nor the last listed Pod is the answer.
    victim = running[len(running) // 2]
    dropped = "printf '#!/bin/sh\\necho checking for updates\\n' > /usr/local/bin/update-check"
    r.require(
        r.kubectl(
            [
                "exec",
                "-n",
                namespace,
                victim,
                "--",
                "sh",
                "-c",
                f"{dropped} && chmod 755 /usr/local/bin/update-check",
            ]
        )
    )
    atomic_write(r.root / "data/tampered-pod.json", json.dumps({"pod": victim}).encode())


def wait_for_default_account(r: LinuxRuntime, namespace: str) -> None:
    existing = r.kubectl(["get", "namespace", namespace])
    if not existing.ok:
        r.require(r.kubectl(["create", "namespace", namespace]))
    deadline = time.monotonic() + 60
    while not r.kubectl(["get", "serviceaccount", "default", "-n", namespace]).ok:
        if time.monotonic() >= deadline:
            raise RuntimeError(f"The default ServiceAccount in {namespace} did not appear.")
        time.sleep(1)


def apply_workspace(r: LinuxRuntime, name: str) -> None:
    """Apply a workspace manifest with this lab's image, as the learner's render step does."""
    r.require(r.kubectl(["apply", "-f", "-"], payload=rendered(Path(name).read_text())))


def rendered(text: str) -> str:
    return re.sub(r"\$\{(DOCKYARD_[A-Z_]+)\}", lambda match: os.environ[match.group(1)], text)


def rolled_out(r: LinuxRuntime, namespace: str, *deployments: str) -> None:
    for deployment in deployments:
        r.require(
            r.kubectl(
                ["rollout", "status", "deployment/" + deployment, "-n", namespace], timeout=180
            )
        )


def exam_a(r: LinuxRuntime) -> None:
    """Cluster and system hardening: every finding comes from a module 25 to 27 lesson."""
    open_kubelet(r, r.worker)
    for manifest in (PUBLIC_STATUS, BROAD_ACCESS, rendered(SECRET_READER), OPEN_EGRESS):
        r.require(r.kubectl(["apply", "-f", "-"], payload=manifest))
    for guest in (r.primary, r.worker):
        metadata_service(r, guest)
    apply_workspace(r, "processing.yaml")
    stage_binaries(r, "kubelet")
    rolled_out(r, "processing", "processor")
    rolled_out(r, "telemetry", "metrics-exporter")


def exam_b(r: LinuxRuntime) -> None:
    """Workload and runtime security: every finding comes from a module 26 to 30 lesson."""
    for guest in (r.primary, r.worker):
        metadata_service(r, guest)
    install_falco_unit(r)
    r.require(r.guest(r.worker, ["sudo", "sh", "-c", LEFTOVERS], input_text=REPORT_SHARE))
    r.require(r.kubectl(["apply", "-f", "-"], payload=rendered(INTRUSION)))
    wait_for_default_account(r, "reports")
    for manifest in ("processing.yaml", "untrusted.yaml", "uploads.yaml", "reports.yaml"):
        apply_workspace(r, manifest)
    rolled_out(r, "processing", "processor", "intake")
    rolled_out(r, "untrusted", "template-preview")
    rolled_out(r, "uploads", "uploader")
    rolled_out(r, "reports", "report-builder", "report-viewer")
    rolled_out(r, "storefront", "catalog")
    tamper(r, "uploads", "app=uploader")
    pod = observed(r, ["get", "pods", "-n", "storefront", "-l", "app=catalog"])["items"][0]
    atomic_write(
        r.root / "data/intrusion-pod.json",
        json.dumps({"name": pod["metadata"]["name"], "uid": pod["metadata"]["uid"]}).encode(),
    )


def prepare(mode: str) -> None:
    r = current()
    record()
    if mode == "benchmark":
        open_kubelet(r, r.worker)
    elif mode == "endpoints":
        for guest in (r.primary, r.worker):
            metadata_service(r, guest)
        r.require(r.kubectl(["apply", "-f", "-"], payload=OPEN_EGRESS))
    elif mode == "binaries":
        stage_binaries(r, "kubectl")
    elif mode == "anonymous":
        r.require(r.kubectl(["apply", "-f", "-"], payload=PUBLIC_STATUS))
    elif mode == "tokens":
        # Kubernetes deletes a legacy token Secret whose ServiceAccount does not exist yet,
        # so the namespace's default account must exist before the manifest is applied.
        wait_for_default_account(r, "reports")
        apply_workspace(r, "reports.yaml")
        for deployment in ("report-builder", "report-viewer"):
            r.require(
                r.kubectl(
                    ["rollout", "status", "deployment/" + deployment, "-n", "reports"],
                    timeout=150,
                )
            )
    elif mode == "rbac":
        r.require(r.kubectl(["apply", "-f", "-"], payload=BROAD_ACCESS))
    elif mode == "access":
        r.require(r.kubectl(["apply", "-f", "-"], payload=ACCESS_REVIEW))
    elif mode == "footprint":
        r.require(r.guest(r.worker, ["sudo", "sh", "-c", LEFTOVERS], input_text=REPORT_SHARE))
    elif mode in {"apparmor", "seccomp"}:
        apply_workspace(r, "processing.yaml")
        for deployment in ("processor", "intake") if mode == "seccomp" else ("processor",):
            r.require(
                r.kubectl(
                    ["rollout", "status", "deployment/" + deployment, "-n", "processing"],
                    timeout=150,
                )
            )
    elif mode == "confine":
        r.require(r.guest(r.primary, ["sudo", "sh", "-c", CONTRACTOR], input_text=DEBUG_SHARE))
        apply_workspace(r, "rendering.yaml")
        r.require(
            r.kubectl(["rollout", "status", "deployment/renderer", "-n", "rendering"], timeout=150)
        )
    elif mode in {"encryption", "wireguard"}:
        # These labs start from the cluster as built: Secrets and Pod traffic unencrypted.
        pass
    elif mode == "sandbox":
        apply_workspace(r, "untrusted.yaml")
        r.require(
            r.kubectl(
                ["rollout", "status", "deployment/template-preview", "-n", "untrusted"],
                timeout=150,
            )
        )
    elif mode == "isolate":
        apply_workspace(r, "plugins.yaml")
        r.require(
            r.kubectl(
                ["rollout", "status", "deployment/plugin-runner", "-n", "plugins"], timeout=150
            )
        )
    elif mode == "audit":
        r.require(r.kubectl(["apply", "-f", "-"], payload=rendered(SECRET_READER)))
        r.require(
            r.kubectl(
                ["rollout", "status", "deployment/metrics-exporter", "-n", "telemetry"],
                timeout=150,
            )
        )
    elif mode == "immutable":
        apply_workspace(r, "uploads.yaml")
        r.require(
            r.kubectl(["rollout", "status", "deployment/uploader", "-n", "uploads"], timeout=150)
        )
        tamper(r, "uploads", "app=uploader")
    elif mode == "falco":
        install_falco_unit(r)
        r.require(r.kubectl(["apply", "-f", "-"], payload=rendered(SHELL_SPAWNER)))
        r.require(
            r.kubectl(["rollout", "status", "deployment/report-sync", "-n", "billing"], timeout=150)
        )
    elif mode == "intrusion":
        for guest in (r.primary, r.worker):
            metadata_service(r, guest)
        install_falco_unit(r)
        r.require(r.kubectl(["apply", "-f", "-"], payload=rendered(INTRUSION)))
        r.require(
            r.kubectl(["rollout", "status", "deployment/catalog", "-n", "storefront"], timeout=150)
        )
        pod = observed(r, ["get", "pods", "-n", "storefront", "-l", "app=catalog"])["items"][0]
        atomic_write(
            r.root / "data/intrusion-pod.json",
            json.dumps({"name": pod["metadata"]["name"], "uid": pod["metadata"]["uid"]}).encode(),
        )
    elif mode == "exam-a":
        exam_a(r)
    elif mode == "exam-b":
        exam_b(r)
    elif mode == "mission":
        open_read_only_port(r, r.worker)
        for guest in (r.primary, r.worker):
            metadata_service(r, guest)
        r.require(r.kubectl(["apply", "-f", "-"], payload=EXCEPT_METADATA))
        stage_binaries(r, "kubeadm")
    else:
        raise ValueError("Unknown CKS lab.")


if __name__ == "__main__":
    prepare(sys.argv[1])
