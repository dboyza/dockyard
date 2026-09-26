#!/bin/sh
set -eu
python helm-values.py
helm upgrade --install dispatch charts/dispatch --namespace staging --create-namespace -f values-practice.yaml -f "$DOCKYARD_STORAGE/helm-values.json" --wait --timeout 120s
