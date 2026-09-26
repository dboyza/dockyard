#!/bin/sh
set -eu
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
sh prepare-tls.sh
kubectl apply -f ingress.yaml
kubectl apply -f gateway.yaml
kubectl apply -f loadbalancer.yaml
