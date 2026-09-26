#!/bin/sh
set -eu
kubectl create configmap prometheus-config --from-file=prometheus.yaml --from-file=rules.yaml --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap metrics-dashboard --from-file=dashboard.json --dry-run=client -o yaml | kubectl apply -f -
python render.py monitoring.yaml | kubectl apply -f -
kubectl rollout restart deployment/prometheus
kubectl rollout status deployment/prometheus --timeout=120s
