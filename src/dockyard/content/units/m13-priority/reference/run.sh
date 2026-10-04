#!/bin/sh
set -eu
# This lab gives the node exactly four "slots", an extended resource, so capacity
# runs out the same way on every computer. Real clusters run out of CPU or memory.
node=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl patch node "$node" --subresource=status --type=json \
  -p '[{"op":"add","path":"/status/capacity/dockyard.io~1slots","value":"4"}]' >/dev/null
python render.py batch.yaml | kubectl apply -f -
kubectl rollout status deployment/report-batch --timeout=90s
if [ -f priority.yaml ]; then
  kubectl apply -f priority.yaml
fi
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/dispatch --timeout=120s
