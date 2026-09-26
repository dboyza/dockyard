#!/bin/sh
set -eu
kubectl kustomize kustomize/overlays/development | python render.py - | kubectl apply -f -
kubectl rollout restart deployment/dispatch
kubectl rollout status deployment/dispatch --timeout=120s
helm rollback dispatch 1 -n staging --wait --timeout 120s
python render.py operator.yaml | kubectl apply -f -
kubectl wait --for=condition=Established crd/workerpools.learning.dockyard.local --timeout=60s
kubectl apply -f pool.yaml
kubectl rollout status deployment/workerpool-controller --timeout=90s
kubectl wait --for=condition=Ready workerpool/dispatch --timeout=120s
python operator-proof.py
