#!/bin/sh
set -eu
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/dispatch --timeout=120s
kubectl rollout status deployment/worker --timeout=120s
kubectl rollout status deployment/inventory --timeout=90s
python render.py preview.yaml | kubectl apply -f -
kubectl rollout restart deployment/dispatch -n preview
kubectl rollout status deployment/dispatch -n preview --timeout=120s
kubectl rollout status deployment/worker -n preview --timeout=120s
