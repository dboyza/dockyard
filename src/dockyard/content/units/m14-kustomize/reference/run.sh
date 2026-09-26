#!/bin/sh
set -eu
kubectl kustomize kustomize/overlays/development | python render.py - | kubectl apply -f -
kubectl rollout restart deployment/dispatch
kubectl rollout status deployment/dispatch --timeout=120s
