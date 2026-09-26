#!/bin/sh
set -eu
docker rm -f "$DOCKYARD_CONTAINER"
docker run -d --name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB" \
  --network "$DOCKYARD_NETWORK" -e UPSTREAM_URL=http://dependency:8080/healthz \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" "$DOCKYARD_IMAGE"
