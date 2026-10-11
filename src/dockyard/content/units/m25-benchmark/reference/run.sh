#!/bin/sh
set -eu
on() { limactl shell --workdir=/tmp "$@"; }
# Read the findings first, as a reviewer would.
on "$DOCKYARD_WORKER" sudo kube-bench run --targets node --benchmark cis-1.12 --check 4.2.1,4.2.2 || true
on "$DOCKYARD_CONTROL_PLANE" sudo kube-bench run --targets master --benchmark cis-1.12 --check 1.2.15 || true
# Worker kubelet: refuse anonymous requests and ask the API server to authorize the rest.
on "$DOCKYARD_WORKER" sudo sed -i -e '/^  anonymous:$/{n;s/enabled: true/enabled: false/;}' -e 's/^  mode: AlwaysAllow$/  mode: Webhook/' /var/lib/kubelet/config.yaml
on "$DOCKYARD_WORKER" sudo systemctl restart kubelet
# API server: turn profiling off in its static Pod manifest; the kubelet restarts it.
on "$DOCKYARD_CONTROL_PLANE" sudo sed -i 's/^    - kube-apiserver$/&\n    - --profiling=false/' /etc/kubernetes/manifests/kube-apiserver.yaml
sh wait-api.sh
kubectl wait --for=condition=Ready "node/lima-$DOCKYARD_WORKER" --timeout=120s
on "$DOCKYARD_WORKER" sudo kube-bench run --targets node --benchmark cis-1.12 --check 4.2.1,4.2.2
on "$DOCKYARD_CONTROL_PLANE" sudo kube-bench run --targets master --benchmark cis-1.12 --check 1.2.15
