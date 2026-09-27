#!/bin/sh
set -eu
kubectl patch deployment dispatch --type=strategic -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","readinessProbe":{"httpGet":{"path":"/readyz","port":"http"}}}]}}}}'
kubectl rollout status deployment/dispatch --timeout=150s
