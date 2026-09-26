#!/bin/sh
set -eu
docker network create --label "io.dockyard.lab=$DOCKYARD_LAB" "$DOCKYARD_NETWORK"
docker network connect --alias dependency "$DOCKYARD_NETWORK" "$DOCKYARD_CONTAINER-dependency"
docker network connect "$DOCKYARD_NETWORK" "$DOCKYARD_CONTAINER"
