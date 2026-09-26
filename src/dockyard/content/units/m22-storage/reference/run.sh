#!/bin/sh
set -eu
kubectl patch statefulset db --type=merge -p "{\"spec\":{\"template\":{\"spec\":{\"nodeSelector\":{\"kubernetes.io/hostname\":\"lima-$DOCKYARD_WORKER\"}}}}}"
kubectl delete pod db-0 --wait=true --timeout=90s
sh bootstrap.sh
