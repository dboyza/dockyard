#!/bin/sh
# Wait until the restarted API server answers and runs with encryption configured.
for attempt in $(seq 1 90); do
  if kubectl get --raw=/readyz >/dev/null 2>&1 &&
    kubectl get pods -n kube-system -l component=kube-apiserver -o jsonpath='{.items[0].spec.containers[0].command}' 2>/dev/null | grep -q -- '--encryption-provider-config='; then
    exit 0
  fi
  sleep 2
done
echo "The API server did not come back with --encryption-provider-config." >&2
exit 1
