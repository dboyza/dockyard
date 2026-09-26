#!/bin/sh
set -eu
for file in storage.yaml admission.yaml settings.yaml identity.yaml platform.yaml worker.yaml clients.yaml network.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status statefulset/db --timeout=150s
for deployment in dispatch queue worker inventory; do
  kubectl rollout status deployment/$deployment --timeout=150s
done
for deployment in trusted-client untrusted-client; do
  kubectl rollout status deployment/$deployment -n frontend --timeout=120s
done
for deployment in outside-client egress-target; do
  kubectl rollout status deployment/$deployment -n dockyard-observer --timeout=120s
done
python -m dockyard.native expose-app
