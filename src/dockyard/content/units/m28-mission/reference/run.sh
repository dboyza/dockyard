#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# A random 32-byte key, encoded as base64, generated on the node so it never touches the workspace.
on "$DOCKYARD_CONTROL_PLANE" sudo sh -c 'mkdir -p /etc/kubernetes/enc && chmod 700 /etc/kubernetes/enc &&
cat > /etc/kubernetes/enc/encryption-config.yaml <<EOC
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
# Point the API server at it and mount the folder into its static Pod.
on "$DOCKYARD_CONTROL_PLANE" sudo python3 - <<'PY'
from pathlib import Path
import yaml
path = Path("/etc/kubernetes/manifests/kube-apiserver.yaml")
pod = yaml.safe_load(path.read_text())
container = pod["spec"]["containers"][0]
container["command"].append("--encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml")
container["volumeMounts"].append({"name": "enc", "mountPath": "/etc/kubernetes/enc", "readOnly": True})
pod["spec"]["volumes"].append(
    {"name": "enc", "hostPath": {"path": "/etc/kubernetes/enc", "type": "DirectoryOrCreate"}}
)
path.write_text(yaml.safe_dump(pod, sort_keys=False))
PY
sh wait-api.sh
kubectl get secrets -A -o json | kubectl replace -f -
# Sandbox: runsc on the worker, a label, and the RuntimeClass the plugins team asked for.
on "$DOCKYARD_WORKER" sudo sh -c 'grep -q "runtimes.runsc\]" /etc/containerd/config.toml || cat >> /etc/containerd/config.toml <<EOC

[plugins."io.containerd.cri.v1.runtime".containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"
EOC
systemctl restart containerd'
kubectl wait --for=condition=Ready "node/lima-$DOCKYARD_WORKER" --timeout=120s
kubectl label node "lima-$DOCKYARD_WORKER" sandbox.dockyard.io/gvisor=true --overwrite
kubectl apply -f runtimeclass.yaml
python render.py plugins.yaml | kubectl apply -f -
kubectl rollout status deployment/plugin-runner -n plugins --timeout=180s
# Encrypt traffic between the nodes.
kubectl patch felixconfigurations.crd.projectcalico.org default --type=merge -p '{"spec":{"wireguardEnabled":true}}'
for attempt in $(seq 1 60); do
  limactl shell --workdir=/tmp "$DOCKYARD_WORKER" ip link show wireguard.cali >/dev/null 2>&1 && break
  sleep 2
done
cp isolation-report-reference.md isolation-report.md
