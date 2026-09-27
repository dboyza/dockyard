#!/bin/sh
set -eu
python repair-pull-secret.py
kubectl rollout restart deployment/dispatch
kubectl rollout status deployment/dispatch --timeout=150s
