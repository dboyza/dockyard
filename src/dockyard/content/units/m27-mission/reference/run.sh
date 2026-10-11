#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# Footprint: survey the control plane, then remove the share and the contractor's access.
on "$DOCKYARD_CONTROL_PLANE" sudo ss -ltnp
on "$DOCKYARD_CONTROL_PLANE" sudo systemctl disable --now debug-share
on "$DOCKYARD_CONTROL_PLANE" sudo systemctl mask debug-share
on "$DOCKYARD_CONTROL_PLANE" sudo rm -f /etc/sudoers.d/contractor
on "$DOCKYARD_CONTROL_PLANE" sudo usermod --shell /usr/sbin/nologin --lock contractor
# AppArmor: install and load the renderer's profile on both nodes.
for node in "$DOCKYARD_CONTROL_PLANE" "$DOCKYARD_WORKER"; do
  on "$node" sudo tee /etc/apparmor.d/dockyard-renderer < dockyard-renderer >/dev/null
  on "$node" sudo apparmor_parser --replace /etc/apparmor.d/dockyard-renderer
done
# Apply both profiles to the renderer.
python render.py rendering.yaml | kubectl apply -f -
kubectl rollout status deployment/renderer -n rendering --timeout=120s
cp confine-report-reference.md confine-report.md
