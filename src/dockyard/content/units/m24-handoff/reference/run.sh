#!/bin/sh
set -eu
kubectl rollout undo deployment/dispatch
kubectl rollout status deployment/dispatch --timeout=150s
