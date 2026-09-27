#!/bin/sh
set -eu
kubectl patch service dispatch --type=merge -p '{"spec":{"selector":{"track":"stable"}}}'
kubectl scale deployment/worker --replicas=1
kubectl rollout status deployment/worker --timeout=120s
