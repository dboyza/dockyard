#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo sh < take-snapshot.sh
python -m dockyard.fixtures.recovery stage-loss
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo sh < restore-snapshot.sh
python wait-control-plane.py
kubectl get nodes
