#!/usr/bin/env bash
# A destructive recovery test confined to the disposable Dockyard probe VM.
set -euo pipefail
test "$(hostname)" = lima-dockyard-probe-cp
export KUBECONFIG=/etc/kubernetes/admin.conf
kubectl create namespace dockyard-recovery-proof
kubectl -n dockyard-recovery-proof create configmap evidence --from-literal=message=snapshot-restored
etcd_pod=etcd-lima-dockyard-probe-cp
kubectl -n kube-system exec "$etcd_pod" -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/lib/etcd/dockyard-proof.db
kubectl -n kube-system exec "$etcd_pod" -- etcdutl snapshot status /var/lib/etcd/dockyard-proof.db -w json
kubectl -n dockyard-recovery-proof delete configmap evidence
test -z "$(kubectl -n dockyard-recovery-proof get configmap evidence --ignore-not-found -o name)"
peer_address=$(hostname -I | awk '{print $1}')
kubectl -n kube-system exec "$etcd_pod" -- etcdutl snapshot restore /var/lib/etcd/dockyard-proof.db \
  --data-dir=/var/lib/etcd/dockyard-restore \
  --name=lima-dockyard-probe-cp \
  --initial-cluster="lima-dockyard-probe-cp=https://${peer_address}:2380" \
  --initial-advertise-peer-urls="https://${peer_address}:2380" \
  --bump-revision=1000000000 --mark-compacted
cp /etc/kubernetes/manifests/etcd.yaml /tmp/dockyard-etcd-before.yaml
python3 - <<'PY'
from pathlib import Path
manifest=Path('/etc/kubernetes/manifests/etcd.yaml')
source=manifest.read_text()
old='path: /var/lib/etcd\n'
assert source.count(old)==1
temporary=Path('/tmp/dockyard-etcd-restored.yaml')
temporary.write_text(source.replace(old,'path: /var/lib/etcd/dockyard-restore\n'))
temporary.replace(manifest)
PY
for attempt in $(seq 1 90); do
  result=$(kubectl --request-timeout=2s -n dockyard-recovery-proof get configmap evidence -o jsonpath='{.data.message}' 2>/dev/null || true)
  if [ "$result" = snapshot-restored ]; then
    printf '%s\n' 'PROOF: a deleted Kubernetes object was recovered from the etcd snapshot.'
    kubectl get nodes
    exit 0
  fi
  sleep 1
done
echo 'Recovery did not meet the deadline.' >&2
exit 1
