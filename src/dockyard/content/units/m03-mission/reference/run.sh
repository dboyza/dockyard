#!/bin/sh
set -eu
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE" .
docker network create --label "io.dockyard.lab=$DOCKYARD_LAB" "$DOCKYARD_NETWORK"
docker run -d --name "$DOCKYARD_CONTAINER-dependency" --label "io.dockyard.lab=$DOCKYARD_LAB" \
  --network "$DOCKYARD_NETWORK" --network-alias dependency "$DOCKYARD_IMAGE"
docker run -d --name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB" \
  --network "$DOCKYARD_NETWORK" -e UPSTREAM_URL=http://dependency:8080/healthz \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" "$DOCKYARD_IMAGE"
