#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo mv /var/lib/dockyard/recovery/kube-scheduler.yaml /etc/kubernetes/manifests/kube-scheduler.yaml
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo systemctl start kubelet
python wait-control-plane.py
kubectl get nodes
