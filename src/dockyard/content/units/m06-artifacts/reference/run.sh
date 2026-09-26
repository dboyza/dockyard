#!/bin/sh
set -eu
docker build --platform linux/arm64 --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE" .
docker rm -f "$DOCKYARD_CONTAINER"
docker run -d --name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB" -p "127.0.0.1:$DOCKYARD_PORT:8080" "$DOCKYARD_IMAGE"
