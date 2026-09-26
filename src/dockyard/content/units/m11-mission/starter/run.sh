#!/bin/sh
set -eu
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status statefulset/db --timeout=120s
DOCKYARD_SEED_ONLY=1 python storage-proof.py
sh backup.sh
