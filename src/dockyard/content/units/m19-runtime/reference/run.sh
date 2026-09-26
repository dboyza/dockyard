#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo tee /etc/crictl.yaml >/dev/null <<'EOF'
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
EOF
