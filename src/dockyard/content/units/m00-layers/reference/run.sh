#!/bin/sh
set -eu
docker run -d \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  "$DOCKYARD_PYTHON_IMAGE" \
  sleep infinity
docker exec "$DOCKYARD_CONTAINER" sh -c 'echo "written in the first container" > /tmp/note.txt'
