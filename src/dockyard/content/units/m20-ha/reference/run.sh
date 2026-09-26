#!/bin/sh
set -eu
python -m dockyard.native lb-config > haproxy.cfg
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo tee /etc/haproxy/haproxy.cfg < haproxy.cfg >/dev/null
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo haproxy -c -f /etc/haproxy/haproxy.cfg
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo systemctl reload haproxy
kubectl get --raw=/readyz
