#!/bin/sh
set -eu
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/dispatch --timeout=120s
python render.py operator.yaml | kubectl apply -f -
kubectl wait --for=condition=Established crd/workerpools.learning.dockyard.local --timeout=60s
kubectl apply -f pool.yaml
kubectl rollout status deployment/workerpool-controller --timeout=90s
kubectl wait --for=condition=Ready workerpool/dispatch --timeout=120s
python operator-proof.py
