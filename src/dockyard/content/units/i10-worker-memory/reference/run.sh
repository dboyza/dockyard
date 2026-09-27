#!/bin/sh
set -eu
kubectl set resources deployment/worker --containers=worker --requests=memory=128Mi --limits=memory=192Mi
kubectl rollout status deployment/worker --timeout=120s
