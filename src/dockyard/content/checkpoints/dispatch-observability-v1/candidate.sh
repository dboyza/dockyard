#!/bin/sh
set -eu
cp VERSION .version-before-candidate
trap 'mv .version-before-candidate VERSION' EXIT HUP INT TERM
cp candidate.VERSION VERSION
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE-candidate" .
kind load docker-image "$DOCKYARD_IMAGE-candidate" --name "$DOCKYARD_CLUSTER"
