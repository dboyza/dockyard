#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo sh < restore-snapshot.sh
python wait-control-plane.py
kubectl rollout status deployment/trusted-client -n frontend --timeout=120s
