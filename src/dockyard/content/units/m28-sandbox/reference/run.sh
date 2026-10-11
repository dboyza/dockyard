#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# Register runsc as a containerd runtime handler on the worker, then restart containerd.
on "$DOCKYARD_WORKER" sudo sh -c 'grep -q "runtimes.runsc\]" /etc/containerd/config.toml || cat >> /etc/containerd/config.toml <<EOC

[plugins."io.containerd.cri.v1.runtime".containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"
EOC
systemctl restart containerd'
kubectl wait --for=condition=Ready "node/lima-$DOCKYARD_WORKER" --timeout=120s
# Mark the node that can run sandboxed Pods, and describe the runtime to Kubernetes.
kubectl label node "lima-$DOCKYARD_WORKER" sandbox.dockyard.io/gvisor=true --overwrite
kubectl apply -f runtimeclass.yaml
python render.py untrusted.yaml | kubectl apply -f -
kubectl rollout status deployment/template-preview -n untrusted --timeout=180s
kubectl exec -n untrusted deploy/template-preview -- dmesg | head -3
