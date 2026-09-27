#!/bin/sh
set -eu
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo mv /var/lib/dockyard/maintenance-exam/kube-scheduler.yaml /etc/kubernetes/manifests/kube-scheduler.yaml
python wait-control-plane.py
kubectl patch service dispatch --type=merge -p '{"spec":{"selector":{"release":null}}}'
kubectl patch networkpolicy allow-dispatch-dependencies --type=json -p '[{"op":"replace","path":"/spec/egress/1/ports/0/port","value":6379}]'
sh upgrade.sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm certs renew apiserver
python restart-api.py
python contracts.py
kubectl rollout status statefulset/db --timeout=150s
kubectl rollout status deployment/dispatch --timeout=150s
kubectl rollout status deployment/worker --timeout=150s
kubectl rollout status deployment/trusted-client -n frontend --timeout=150s
