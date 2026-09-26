#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo sysctl -w net.ipv4.ip_forward=1
kubectl patch deployment trusted-client -n frontend --type=merge -p '{"spec":{"template":{"spec":{"dnsPolicy":"ClusterFirst"}}}}'
kubectl patch statefulset db --type=merge -p "{\"spec\":{\"template\":{\"spec\":{\"nodeSelector\":{\"kubernetes.io/hostname\":\"lima-$DOCKYARD_WORKER\"}}}}}"
kubectl delete pod db-0 --wait=true --timeout=90s
sh bootstrap.sh
