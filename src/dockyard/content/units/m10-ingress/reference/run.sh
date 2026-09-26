#!/bin/sh
set -eu
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
sh prepare-tls.sh
kubectl apply -f ingress.yaml
kubectl rollout status deployment/dispatch --timeout=120s
