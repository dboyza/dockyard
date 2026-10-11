#!/bin/sh
set -eu
# Analyse what will actually be deployed: the rendered manifest.
python render.py resizer.yaml | kube-linter lint - || true
python render.py resizer.yaml | kubesec scan - | python -c 'import json,sys; [print(r["object"], r["score"]) for r in json.load(sys.stdin)]'
for file in settings.yaml identity.yaml platform.yaml worker.yaml agent.yaml maintenance.yaml resizer.yaml; do
  python render.py "$file" | kubectl apply -f -
done
kubectl rollout status deployment/resizer -n media --timeout=120s
python render.py resizer.yaml | kube-linter lint -
