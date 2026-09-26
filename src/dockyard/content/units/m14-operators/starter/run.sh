#!/bin/sh
set -eu
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
python render.py operator.yaml | kubectl apply -f -
kubectl wait --for=condition=Established crd/workerpools.learning.dockyard.local --timeout=60s
kubectl apply -f pool.yaml
