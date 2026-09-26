#!/bin/sh
set -eu
kubectl label nodes -l '!node-role.kubernetes.io/control-plane' dockyard.pool=apps --overwrite
kubectl taint nodes -l dockyard.pool=apps dockyard.pool=apps:NoSchedule --overwrite
kubectl apply -f capacity.yaml
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/dispatch --timeout=120s
