#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo tee /etc/crictl.yaml >/dev/null <<'EOF'
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
EOF
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo systemctl start kubelet
kubectl wait --for=condition=Ready nodes --all --timeout=120s
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sh -c 'sudo install -m 600 -o "$(id -u)" -g "$(id -g)" /etc/kubernetes/admin.conf "$HOME/.kube/operator.conf"'
