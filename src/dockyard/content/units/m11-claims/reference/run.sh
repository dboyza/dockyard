#!/bin/sh
set -eu
kubectl apply -f claim.yaml
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/db --timeout=120s
python storage-proof.py
kubectl rollout status deployment/dispatch --timeout=120s
