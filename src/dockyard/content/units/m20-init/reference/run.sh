#!/bin/sh
set -eu
umask 077
python -m dockyard.native init-config > init.yaml
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm init --config=/dev/stdin < init.yaml
python -m dockyard.native refresh-client
