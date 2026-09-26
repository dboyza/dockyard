#!/bin/sh
set -eu
for file in settings.yaml identity.yaml dependencies.yaml worker.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status statefulset/db --timeout=120s
kubectl rollout status deployment/queue --timeout=120s
python pipeline.py
python gitops.py seed
kubectl apply -f deployer.yaml
python render.py flux.yaml | kubectl apply -f -
