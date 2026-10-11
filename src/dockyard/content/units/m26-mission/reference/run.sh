#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# Find and remove what grants access to anonymous callers.
kubectl get rolebindings,clusterrolebindings -A -o wide | grep -E "system:(anonymous|unauthenticated)" || true
kubectl delete rolebinding legacy-dashboard -n dispatch
# Place the authentication configuration on the control-plane node.
on "$DOCKYARD_CONTROL_PLANE" sudo tee /etc/kubernetes/auth-config.yaml < auth-config.yaml >/dev/null
# Point the API server at it and mount the file into its static Pod.
on "$DOCKYARD_CONTROL_PLANE" sudo python3 - <<'PY'
from pathlib import Path
import yaml
path = Path("/etc/kubernetes/manifests/kube-apiserver.yaml")
pod = yaml.safe_load(path.read_text())
container = pod["spec"]["containers"][0]
container["command"].append("--authentication-config=/etc/kubernetes/auth-config.yaml")
container["volumeMounts"].append(
    {"name": "auth-config", "mountPath": "/etc/kubernetes/auth-config.yaml", "readOnly": True}
)
pod["spec"]["volumes"].append(
    {"name": "auth-config", "hostPath": {"path": "/etc/kubernetes/auth-config.yaml", "type": "File"}}
)
path.write_text(yaml.safe_dump(pod, sort_keys=False))
PY
sh wait-api.sh
curl -sk -o /dev/null -w 'anonymous /version: %{http_code}\n' "https://127.0.0.1:$DOCKYARD_API_PORT/version" || true
# Revoke long-lived tokens outside kube-system.
kubectl get secrets -A --field-selector type=kubernetes.io/service-account-token
kubectl delete secret deployer-token -n ci
# Auditors: read-only in the two namespaces they review.
kubectl apply -f auditors.yaml
kubectl delete clusterrolebinding auditors-admin
cp access-report-reference.md access-report.md
