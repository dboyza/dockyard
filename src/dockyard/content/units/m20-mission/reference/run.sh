#!/bin/sh
set -eu
umask 077
python -m dockyard.native init-config > init.yaml
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm init --config=/dev/stdin < init.yaml
python -m dockyard.native refresh-client
umask 077
python -m dockyard.native join-config "$DOCKYARD_WORKER" > join.yaml
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo kubeadm join --config=/dev/stdin < join.yaml
rm join.yaml
python -m dockyard.native network-manifest > calico.yaml
kubectl apply -f calico.yaml
kubectl wait --for=condition=Ready nodes --all --timeout=240s
kubectl rollout status daemonset/calico-node -n kube-system --timeout=240s
kubectl rollout status deployment/coredns -n kube-system --timeout=240s
sh bootstrap.sh
