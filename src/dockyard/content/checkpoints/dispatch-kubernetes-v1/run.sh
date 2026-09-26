#!/bin/sh
set -eu
python render.py deployment.yaml | kubectl apply -f -
kubectl apply -f service.yaml
