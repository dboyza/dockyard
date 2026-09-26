#!/bin/sh
set -eu
python measure-slo.py before
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout restart deployment/dispatch
kubectl rollout status deployment/dispatch --timeout=120s
sh monitoring.sh
python alert-proof.py
python measure-slo.py after
