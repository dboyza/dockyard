#!/bin/sh
set -eu
kubectl apply -f capacity.yaml
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl apply -f autoscale.yaml
python render.py load.yaml | kubectl apply -f -
