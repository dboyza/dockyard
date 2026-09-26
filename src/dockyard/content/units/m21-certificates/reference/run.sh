#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm certs check-expiration
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm certs renew apiserver
python restart-api.py
kubectl get --raw=/readyz
