#!/bin/sh
set -eu
python helm-values.py
helm upgrade --install dispatch charts/dispatch -n staging --create-namespace -f values-practice.yaml -f "$DOCKYARD_STORAGE/helm-values.json" --set api.replicas=2 --wait --timeout 120s
/bin/sh release.sh
