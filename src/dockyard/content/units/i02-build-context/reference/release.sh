#!/bin/sh
set -eu
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" --label "io.dockyard.lab=$DOCKYARD_LAB" -f Dockerfile -t "$DOCKYARD_IMAGE" .
