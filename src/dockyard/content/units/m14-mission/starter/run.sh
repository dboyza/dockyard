#!/bin/sh
set -eu
kubectl kustomize kustomize/overlays/development | python render.py - | kubectl apply -f -
python helm-values.py
helm upgrade --install dispatch charts/dispatch -n staging --create-namespace -f values-practice.yaml -f "$DOCKYARD_STORAGE/helm-values.json" --set api.replicas=2 --wait --timeout 120s
/bin/sh release.sh
python render.py operator.yaml | kubectl apply -f -
kubectl wait --for=condition=Established crd/workerpools.learning.dockyard.local --timeout=60s
kubectl apply -f pool.yaml
