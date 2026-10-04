#!/bin/sh
set -eu
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" \
  --secret id=release_token,src=release-token.txt \
  --label "io.dockyard.lab=$DOCKYARD_LAB" -t "$DOCKYARD_IMAGE" .
