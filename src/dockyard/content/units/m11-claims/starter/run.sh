#!/bin/sh
set -eu
kubectl apply -f claim.yaml
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
