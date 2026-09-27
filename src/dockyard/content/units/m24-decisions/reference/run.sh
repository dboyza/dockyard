#!/bin/sh
set -eu
python render.py identity.yaml | kubectl apply -f -
kubectl scale deployment/dispatch --replicas=2
kubectl apply -f operations-budget.yaml
kubectl rollout status deployment/dispatch --timeout=120s
