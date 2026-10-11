#!/bin/sh
# Wait until the restarted API server answers with all three configurations in place.
for attempt in $(seq 1 120); do
  command=$(kubectl get pods -n kube-system -l component=kube-apiserver -o jsonpath='{.items[0].spec.containers[0].command}' 2>/dev/null || true)
  if kubectl get --raw=/readyz >/dev/null 2>&1 &&
    echo "$command" | grep -q -- '--authentication-config=' &&
    echo "$command" | grep -q -- '--encryption-provider-config=' &&
    echo "$command" | grep -q -- '--audit-policy-file='; then
    exit 0
  fi
  sleep 2
done
echo "The API server did not come back with every configuration." >&2
exit 1
