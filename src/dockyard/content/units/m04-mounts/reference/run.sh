#!/bin/sh
set -eu
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE" .
mkdir -p "$DOCKYARD_STORAGE"
docker run -d --name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB" --user "$(id -u):$(id -g)" -p "127.0.0.1:$DOCKYARD_PORT:8080" --mount "type=bind,source=$DOCKYARD_STORAGE,target=/data" "$DOCKYARD_IMAGE"
