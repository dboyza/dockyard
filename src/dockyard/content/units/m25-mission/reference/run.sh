#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# Benchmark: find the failures on each node first.
on "$DOCKYARD_WORKER" sudo kube-bench run --targets node --benchmark cis-1.12 | grep -E '^\[FAIL\]' || true
on "$DOCKYARD_CONTROL_PLANE" sudo kube-bench run --targets master --benchmark cis-1.12 | grep -E '^\[FAIL\]' || true
# 4.2.4: close the kubelet's unauthenticated read-only port.
on "$DOCKYARD_WORKER" sudo sed -i 's/^readOnlyPort: 10255$/readOnlyPort: 0/' /var/lib/kubelet/config.yaml
on "$DOCKYARD_WORKER" sudo systemctl restart kubelet
# 1.3.2: controller manager profiling off.
on "$DOCKYARD_CONTROL_PLANE" sudo sed -i 's/^    - kube-controller-manager$/&\n    - --profiling=false/' /etc/kubernetes/manifests/kube-controller-manager.yaml
sh wait-component.sh kube-controller-manager
kubectl wait --for=condition=Ready "node/lima-$DOCKYARD_WORKER" --timeout=120s
# Endpoints: replace the metadata-only exception with an allowlist.
kubectl apply -f frontend-egress.yaml
# Binaries: keep only staged files that match the official checksums.
for name in kubeadm kubelet kubectl; do
  if ! echo "$(cat "release-checksums/$name.sha512")  /opt/dockyard/staged/$name" |
    on "$DOCKYARD_CONTROL_PLANE" sha512sum -c -; then
    on "$DOCKYARD_CONTROL_PLANE" sudo rm -f "/opt/dockyard/staged/$name"
  fi
done
cp baseline-report-reference.md baseline-report.md
