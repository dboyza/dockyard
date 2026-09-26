#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo systemctl start kubelet
kubectl wait --for=condition=Ready nodes --all --timeout=120s
