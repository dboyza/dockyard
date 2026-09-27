#!/bin/sh
set -eu
python -m dockyard.native stage-upgrade
packages="/tmp/dockyard-$DOCKYARD_LAB-upgrade"
for guest in "$DOCKYARD_CONTROL_PLANE" "$DOCKYARD_WORKER"; do
  limactl shell --workdir=/tmp "$guest" sudo apt-mark unhold kubeadm
  limactl shell --workdir=/tmp "$guest" sudo dpkg -i "$packages/kubeadm_1.35.8-1.1_arm64.deb"
  limactl shell --workdir=/tmp "$guest" sudo apt-mark hold kubeadm
  if [ "$guest" = "$DOCKYARD_CONTROL_PLANE" ]; then
    limactl shell --workdir=/tmp "$guest" sudo kubeadm upgrade plan v1.35.8
    limactl shell --workdir=/tmp "$guest" sudo kubeadm upgrade apply v1.35.8 --yes
  else
    limactl shell --workdir=/tmp "$guest" sudo kubeadm upgrade node
  fi
  kubectl drain "lima-$guest" --ignore-daemonsets --delete-emptydir-data --timeout=180s
  limactl shell --workdir=/tmp "$guest" sudo apt-mark unhold kubelet kubectl
  limactl shell --workdir=/tmp "$guest" sudo dpkg -i "$packages/kubelet_1.35.8-1.1_arm64.deb" "$packages/kubectl_1.35.8-1.1_arm64.deb"
  limactl shell --workdir=/tmp "$guest" sudo apt-mark hold kubelet kubectl
  limactl shell --workdir=/tmp "$guest" sudo systemctl daemon-reload
  limactl shell --workdir=/tmp "$guest" sudo systemctl restart kubelet
  python -m dockyard.native wait-upgraded-node "$guest"
  kubectl uncordon "lima-$guest"
done
kubectl wait --for=condition=Ready nodes --all --timeout=180s
python -m dockyard.native refresh-client

