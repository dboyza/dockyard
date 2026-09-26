#!/bin/sh
set -eu
kubectl patch pdb dispatch-maintenance --type=merge -p '{"spec":{"minAvailable":1}}'
kubectl drain "lima-$DOCKYARD_NODE_PREFIX-worker2" --ignore-daemonsets --delete-emptydir-data --timeout=180s
kubectl rollout status deployment/dispatch --timeout=180s
