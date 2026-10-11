#!/bin/sh
set -eu
kubectl patch felixconfigurations.crd.projectcalico.org default --type=merge -p '{"spec":{"wireguardEnabled":true}}'
# Wait until both nodes publish a public key and have the tunnel interface.
for attempt in $(seq 1 60); do
  keys=$(kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.annotations.projectcalico\.org/WireguardPublicKey}{"\n"}{end}' | grep -c . || true)
  if [ "$keys" = 2 ] &&
    limactl shell --workdir=/tmp "$DOCKYARD_WORKER" ip link show wireguard.cali >/dev/null 2>&1 &&
    limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" ip link show wireguard.cali >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" ip -s link show wireguard.cali
