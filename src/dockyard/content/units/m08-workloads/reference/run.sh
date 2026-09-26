#!/bin/sh
set -eu
for file in platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/worker --timeout=120s
kubectl rollout status daemonset/dispatch-node-agent --timeout=90s
