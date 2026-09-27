#!/bin/sh
set -eu
docker build --build-arg BASE_IMAGE="$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE-release" .
kind load docker-image "$DOCKYARD_IMAGE-release" --name "$DOCKYARD_CLUSTER"
kubectl set image deployment/dispatch api="$DOCKYARD_IMAGE-release"
kubectl patch configmap dispatch-settings --type=merge -p '{"data":{"environment":"assessment","banner.txt":"Dispatch release accepted"}}'
kubectl patch deployment dispatch --type=strategic -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","readinessProbe":{"httpGet":{"path":"/readyz","port":8080}}}]}}}}'
kubectl rollout restart deployment/dispatch
kubectl rollout status deployment/dispatch --timeout=150s
kubectl patch service dispatch --type=merge -p '{"spec":{"ports":[{"port":8080,"targetPort":8080}]}}'
kubectl patch cronjob release-audit --type=merge -p '{"spec":{"schedule":"17 2 * * *","timeZone":"Etc/UTC","suspend":false,"concurrencyPolicy":"Forbid"}}'
kubectl create job release-audit-proof --from=cronjob/release-audit
kubectl wait job/release-audit-proof --for=condition=Complete --timeout=90s
kubectl patch deployment reporter --type=merge -p '{"spec":{"template":{"spec":{"volumes":[{"name":"reports","persistentVolumeClaim":{"claimName":"reports"}}]}}}}'
kubectl rollout status deployment/reporter --timeout=120s
python render.py audit-tail.yaml | kubectl apply -f -
kubectl wait pod/audit-tail --for=condition=Ready --timeout=90s
kubectl patch networkpolicy audit-access --type=merge -p '{"spec":{"ingress":[{"from":[{"podSelector":{"matchLabels":{"role":"audit-reader"}}}],"ports":[{"protocol":"TCP","port":8080}]}]}}'
