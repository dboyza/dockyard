#!/bin/sh
set -eu
kubectl kustomize kustomize/overlays/development | python render.py - | kubectl apply -f -
