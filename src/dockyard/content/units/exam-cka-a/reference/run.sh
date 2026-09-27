#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo sysctl -w net.ipv4.ip_forward=1
kubectl patch deployment trusted-client -n frontend --type=merge -p '{"spec":{"template":{"spec":{"dnsPolicy":"ClusterFirst"}}}}'
python repair.py
kubectl rollout status statefulset/db --timeout=150s
kubectl rollout status deployment/batch-audit --timeout=150s
helm upgrade --install operations-report ./ops-chart -n dispatch --set environment=production --wait --timeout=150s
python snapshot.py
kubectl rollout status daemonset/node-observer --timeout=150s
kubectl rollout status deployment/trusted-client -n frontend --timeout=150s
