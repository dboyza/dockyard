#!/bin/sh
set -eu
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml; do
  python render.py "$file" | kubectl apply -f -
done
sh candidate.sh
python render.py canary.yaml | kubectl apply -f -
kubectl apply -f preview.yaml
