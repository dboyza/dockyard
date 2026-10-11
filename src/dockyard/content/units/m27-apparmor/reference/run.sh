#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
for node in "$DOCKYARD_CONTROL_PLANE" "$DOCKYARD_WORKER"; do
  # Install the profile where AppArmor loads it at boot, and load it now.
  on "$node" sudo tee /etc/apparmor.d/dockyard-processor < dockyard-processor >/dev/null
  on "$node" sudo apparmor_parser --replace /etc/apparmor.d/dockyard-processor
  on "$node" sudo aa-status | grep dockyard-processor
done
python render.py processing.yaml | kubectl apply -f -
kubectl rollout status deployment/processor -n processing --timeout=120s
kubectl exec -n processing deploy/processor -- cat /proc/1/attr/apparmor/current
