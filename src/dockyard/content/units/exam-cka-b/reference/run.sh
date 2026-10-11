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
# Check the result like a careful candidate: Pods started while the API server restarted
# pass NetworkPolicy only once the network plugin has caught up, so test the request path.
backends='import socket; [socket.create_connection(t, 2).close() for t in (("db", 5432), ("queue", 6379))]'
api='import urllib.request; urllib.request.urlopen("http://dispatch.dispatch.svc.cluster.local:8080/healthz", timeout=2)'
reachable() {
  pods=$(kubectl get pods -n "$1" -l "$2" -o name)
  [ -n "$pods" ] || return 1
  for pod in $pods; do
    kubectl exec -n "$1" "$pod" -- python -c "$3" 2>/dev/null || return 1
  done
}
for attempt in $(seq 1 60); do
  if reachable dispatch app=worker "$backends" && reachable dispatch app=dispatch "$backends" &&
    reachable frontend app=trusted "$api"; then
    exit 0
  fi
  sleep 3
done
echo "The workloads still cannot reach their dependencies." >&2
exit 1
