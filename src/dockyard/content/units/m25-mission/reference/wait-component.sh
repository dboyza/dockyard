#!/bin/sh
# Usage: wait-component.sh COMPONENT - wait until a control-plane Pod is ready with profiling off.
for attempt in $(seq 1 90); do
  if kubectl get pods -n kube-system -l "component=$1" -o jsonpath='{.items[0].spec.containers[0].command}' 2>/dev/null | grep -q -- '--profiling=false' &&
    [ "$(kubectl get pods -n kube-system -l "component=$1" -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>/dev/null)" = true ]; then
    exit 0
  fi
  sleep 2
done
echo "$1 did not come back ready with --profiling=false." >&2
exit 1
