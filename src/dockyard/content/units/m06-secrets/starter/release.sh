#!/bin/sh
set -eu
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" \
  --build-arg "RELEASE_TOKEN=$(cat release-token.txt)" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" -t "$DOCKYARD_IMAGE" .
