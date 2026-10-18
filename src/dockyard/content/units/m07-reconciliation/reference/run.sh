#!/bin/sh
set -eu
python render.py deployment.yaml | kubectl apply -f -
kubectl apply -f service.yaml
kubectl rollout status deployment/dispatch --timeout=120s
# Remove one copy and let the ReplicaSet create its replacement.
pod="$(kubectl get pods -l app=dispatch -o jsonpath='{.items[0].metadata.name}')"
kubectl delete pod "$pod" --wait=true
kubectl rollout status deployment/dispatch --timeout=120s
