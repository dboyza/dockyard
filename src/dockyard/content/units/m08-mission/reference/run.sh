#!/bin/sh
set -eu
for file in platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/worker --timeout=120s
kubectl rollout status daemonset/dispatch-node-agent --timeout=90s
kubectl delete job maintenance-proof --ignore-not-found
kubectl create job maintenance-proof --from=cronjob/dispatch-maintenance
kubectl wait --for=condition=Complete job/maintenance-proof --timeout=120s
