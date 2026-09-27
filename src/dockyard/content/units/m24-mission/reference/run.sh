#!/bin/sh
set -eu
python -m dockyard.native lb-config > haproxy.cfg
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo tee /etc/haproxy/haproxy.cfg < haproxy.cfg >/dev/null
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo haproxy -c -f /etc/haproxy/haproxy.cfg
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo systemctl reload haproxy
kubectl get --raw=/readyz
kubectl patch service dispatch --type=merge -p '{"spec":{"selector":{"track":"stable"}}}'
kubectl scale deployment/worker --replicas=1
kubectl rollout status deployment/worker --timeout=120s
python render.py identity.yaml | kubectl apply -f -
kubectl scale deployment/dispatch --replicas=2
kubectl apply -f operations-budget.yaml
kubectl rollout status deployment/dispatch --timeout=120s
printf '%s\n' dispatch-handoff-v1 > VERSION
python build.py
kubectl rollout restart deployment/dispatch deployment/worker
kubectl rollout status deployment/dispatch --timeout=150s
kubectl rollout status deployment/worker --timeout=150s
