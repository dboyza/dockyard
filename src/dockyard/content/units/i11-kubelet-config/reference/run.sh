#!/bin/sh
set -eu
python repair-node.py
python wait-control-plane.py
kubectl wait nodes --all --for=condition=Ready --timeout=120s
kubectl rollout status statefulset/db --timeout=150s
kubectl rollout status deployment/dispatch --timeout=150s
kubectl rollout status deployment/worker --timeout=150s
kubectl rollout status deployment/trusted-client -n frontend --timeout=150s
