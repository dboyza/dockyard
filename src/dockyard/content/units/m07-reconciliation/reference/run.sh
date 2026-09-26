#!/bin/sh
set -eu
python render.py deployment.yaml | kubectl apply -f -
kubectl apply -f service.yaml
kubectl rollout status deployment/dispatch --timeout=120s
