#!/bin/sh
set -eu
docker rm -f "$DOCKYARD_CONTAINER"
docker run -d --name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" --read-only --cap-drop ALL \
  --security-opt no-new-privileges --memory 128m --cpus 0.5 --pids-limit 64 "$DOCKYARD_IMAGE"
