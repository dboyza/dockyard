#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# 1. Worker kubelet: no anonymous access, Webhook authorization.
on "$DOCKYARD_WORKER" sudo sed -i -e '/^  anonymous:$/{n;s/enabled: true/enabled: false/;}' -e 's/^  mode: AlwaysAllow$/  mode: Webhook/' /var/lib/kubelet/config.yaml
on "$DOCKYARD_WORKER" sudo systemctl restart kubelet
# 3. CI deployer: namespaced access only.
kubectl apply -f rbac.yaml
kubectl delete clusterrolebinding ci-deployer-admin
# 2, 5, 8. Files for the API server: authentication, encryption, and audit configuration.
kubectl delete clusterrolebinding public-status
kubectl delete clusterrole status-reader
on "$DOCKYARD_CONTROL_PLANE" sudo mkdir -p /etc/kubernetes/enc /etc/kubernetes/audit /var/log/kubernetes/audit
on "$DOCKYARD_CONTROL_PLANE" sudo chmod 700 /etc/kubernetes/enc
on "$DOCKYARD_CONTROL_PLANE" sudo tee /etc/kubernetes/auth-config.yaml < auth-config.yaml >/dev/null
on "$DOCKYARD_CONTROL_PLANE" sudo tee /etc/kubernetes/audit/policy.yaml < audit-policy.yaml >/dev/null
on "$DOCKYARD_CONTROL_PLANE" sudo sh -c 'cat > /etc/kubernetes/enc/encryption-config.yaml <<EOC
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: $(head -c 32 /dev/urandom | base64)
  - identity: {}
EOC
chmod 600 /etc/kubernetes/enc/encryption-config.yaml'
# One manifest edit, so the API server restarts once.
on "$DOCKYARD_CONTROL_PLANE" sudo python3 - <<'PY'
from pathlib import Path
import yaml
path = Path("/etc/kubernetes/manifests/kube-apiserver.yaml")
pod = yaml.safe_load(path.read_text())
container = pod["spec"]["containers"][0]
container["command"] += [
    "--authentication-config=/etc/kubernetes/auth-config.yaml",
    "--encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml",
    "--audit-policy-file=/etc/kubernetes/audit/policy.yaml",
    "--audit-log-path=/var/log/kubernetes/audit/audit.log",
    "--audit-log-maxage=7",
    "--audit-log-maxbackup=3",
    "--audit-log-maxsize=50",
]
mounts = [
    ("auth-config", "/etc/kubernetes/auth-config.yaml", "File", True),
    ("enc", "/etc/kubernetes/enc", "DirectoryOrCreate", True),
    ("audit-policy", "/etc/kubernetes/audit/policy.yaml", "File", True),
    ("audit-log", "/var/log/kubernetes/audit", "DirectoryOrCreate", False),
]
for name, target, kind, read_only in mounts:
    container["volumeMounts"].append({"name": name, "mountPath": target, "readOnly": read_only})
    pod["spec"]["volumes"].append({"name": name, "hostPath": {"path": target, "type": kind}})
path.write_text(yaml.safe_dump(pod, sort_keys=False))
PY
sh wait-api.sh
kubectl get secrets -A -o json | kubectl replace -f -
# 4. AppArmor on both nodes, then the processor under it.
for node in "$DOCKYARD_CONTROL_PLANE" "$DOCKYARD_WORKER"; do
  on "$node" sudo tee /etc/apparmor.d/dockyard-processor < dockyard-processor >/dev/null
  on "$node" sudo apparmor_parser --replace /etc/apparmor.d/dockyard-processor
done
python render.py processing.yaml | kubectl apply -f -
kubectl rollout status deployment/processor -n processing --timeout=120s
# 6. Frontend egress allowlist.
kubectl apply -f frontend-egress.yaml
# 7. Staged binaries: keep only exact matches.
for name in kubeadm kubelet kubectl; do
  if ! echo "$(cat "release-checksums/$name.sha512")  /opt/dockyard/staged/$name" |
    on "$DOCKYARD_CONTROL_PLANE" sha512sum -c -; then
    on "$DOCKYARD_CONTROL_PLANE" sudo rm -f "/opt/dockyard/staged/$name"
  fi
done
kubectl wait --for=condition=Ready "node/lima-$DOCKYARD_WORKER" --timeout=120s
# 8. The reader runs every 20 seconds; list who reads the Secret until a workload's account appears.
for attempt in $(seq 1 60); do
  readers=$(on "$DOCKYARD_CONTROL_PLANE" sudo sh -c 'grep "\"resource\":\"secrets\"" /var/log/kubernetes/audit/audit.log | grep "dispatch-database"' |
    python3 -c 'import json,sys; print(sorted({json.loads(l)["user"]["username"] for l in sys.stdin if l.strip()}))')
  case "$readers" in *serviceaccount*) break ;; esac
  sleep 5
done
echo "$readers"
case "$readers" in *serviceaccount*) ;; *) echo "No workload read the Secret within five minutes." >&2; exit 1 ;; esac
echo "system:serviceaccount:telemetry:metrics-exporter" > finding.txt
