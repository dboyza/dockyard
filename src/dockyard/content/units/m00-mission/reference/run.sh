#!/bin/sh
set -eu
docker rm -f "$DOCKYARD_CONTAINER"
docker run -d \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8000" \
  -v "$DOCKYARD_WORKSPACE/welcome:/srv:ro" \
  -w /srv \
  "$DOCKYARD_PYTHON_IMAGE" \
  python -m http.server 8000
