#!/bin/sh
set -eu
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status statefulset/db --timeout=120s
kubectl rollout status deployment/dispatch --timeout=120s
python termination-proof.py
sh candidate.sh
python render.py canary.yaml | kubectl apply -f -
kubectl apply -f preview.yaml
kubectl rollout status deployment/dispatch-canary --timeout=120s
