#!/bin/sh
set -eu
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/dispatch --timeout=120s
kubectl rollout status deployment/worker --timeout=120s
pod=$(kubectl get pods -l app=dispatch -o jsonpath='{.items[0].metadata.name}')
name="inspect-$(date +%s)"
kubectl debug "$pod" --image="$DOCKYARD_BUSYBOX_LOCAL_IMAGE" --target=api --profile=general -c "$name" -- ps
for attempt in $(seq 1 30); do
  finished=$(kubectl get pod "$pod" -o jsonpath="{.status.ephemeralContainerStatuses[?(@.name==\"$name\")].state.terminated.reason}")
  [ -n "$finished" ] && break
  sleep 2
done
kubectl logs "$pod" -c "$name" > api-processes.txt
cat api-processes.txt
