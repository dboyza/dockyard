#!/bin/sh
set -eu
kubectl apply -f frontend-egress.yaml
kubectl get networkpolicy -n frontend frontend-egress -o yaml
