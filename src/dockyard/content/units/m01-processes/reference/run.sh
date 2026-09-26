#!/bin/sh
set -eu
docker run -d \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" \
  -v "$DOCKYARD_WORKSPACE:/app:ro" \
  -w /app \
  "$DOCKYARD_PYTHON_IMAGE" python app.py
