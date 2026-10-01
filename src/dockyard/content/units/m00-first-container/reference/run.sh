#!/bin/sh
set -eu
docker run \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  "$DOCKYARD_PYTHON_IMAGE" \
  python -c "print('Hello from inside a container')"
