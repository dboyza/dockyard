#!/bin/sh
set -eu
docker run -d \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8000" \
  -v "$DOCKYARD_WORKSPACE/site:/site:ro" \
  -w /site \
  "$DOCKYARD_PYTHON_IMAGE" \
  python -m http.server 8000
