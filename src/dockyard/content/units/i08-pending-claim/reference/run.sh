#!/bin/sh
set -eu
kubectl patch deployment archiver --type=merge -p '{"spec":{"template":{"spec":{"nodeSelector":{"dockyard.io/storage-tier":"warm"}}}}}'
kubectl rollout status deployment/archiver --timeout=150s
