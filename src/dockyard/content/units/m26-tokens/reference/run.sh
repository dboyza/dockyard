#!/bin/sh
set -eu
# What can the default ServiceAccount do, and which tokens exist?
kubectl auth can-i --list -n reports --as=system:serviceaccount:reports:default | head -15
kubectl get secrets -n reports --field-selector type=kubernetes.io/service-account-token
# Remove what the corrected manifest no longer contains, then apply it.
kubectl delete rolebinding reports-default-edit -n reports
kubectl delete secret default-token-legacy -n reports
python render.py reports.yaml | kubectl apply -f -
# Pods pick up a new identity and token settings only when they are recreated.
kubectl rollout restart deployment/report-viewer -n reports
kubectl rollout status deployment/report-builder -n reports --timeout=120s
kubectl rollout status deployment/report-viewer -n reports --timeout=120s
kubectl auth can-i get configmap/report-settings -n reports --as=system:serviceaccount:reports:report-builder
