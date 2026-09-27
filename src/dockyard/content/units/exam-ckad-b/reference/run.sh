#!/bin/sh
set -eu
python pin.py
kubectl set env deployment/dispatch DB_PASSWORD_FILE=/var/run/dispatch/password
kubectl patch deployment dispatch --type=merge -p '{"spec":{"template":{"spec":{"automountServiceAccountToken":false}}}}'
kubectl patch deployment worker --type=strategic -p '{"spec":{"replicas":2,"template":{"spec":{"containers":[{"name":"worker","resources":{"requests":{"cpu":"50m","memory":"64Mi"},"limits":{"cpu":"300m","memory":"192Mi"}}}]}}}}'
python overlay.py
kubectl apply -k release/overlays/production
kubectl set image deployment/preview-api api="$DOCKYARD_IMAGE-preview"
kubectl patch deployment preview-api --type=merge -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxUnavailable":0,"maxSurge":1}}}}'
kubectl set env deployment/report-listener PORT=8090
kubectl patch service reports --type=merge -p '{"spec":{"ports":[{"port":8080,"targetPort":8090}]}}'
kubectl exec -i deployment/report-cache -- python -c "import sys; from pathlib import Path; Path('/archive/report.json').write_bytes(sys.stdin.buffer.read())" < report-backup.json
kubectl patch service preview --type=merge -p '{"spec":{"selector":{"app":"preview-api"}}}'
for name in dispatch worker metadata-reader preview-api report-listener; do
 kubectl rollout status deployment/$name --timeout=150s
done
