#!/bin/sh
set -eu
for file in settings.yaml identity.yaml initial-platform.yaml worker.yaml agent.yaml maintenance.yaml; do
 python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/dispatch --timeout=120s
python render.py platform.yaml | kubectl apply -f -
