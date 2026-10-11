#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
for node in "$DOCKYARD_CONTROL_PLANE" "$DOCKYARD_WORKER"; do
  # Localhost profiles are read from the kubelet's seccomp folder on each node.
  on "$node" sudo mkdir -p /var/lib/kubelet/seccomp/profiles
  on "$node" sudo tee /var/lib/kubelet/seccomp/profiles/no-chmod.json < profiles/no-chmod.json >/dev/null
done
python render.py processing.yaml | kubectl apply -f -
kubectl rollout status deployment/processor -n processing --timeout=120s
kubectl rollout status deployment/intake -n processing --timeout=120s
kubectl exec -n processing deploy/processor -- grep Seccomp: /proc/1/status
