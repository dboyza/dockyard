#!/bin/sh
set -eu
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" -v "$DOCKYARD_VOLUME:/data" "$DOCKYARD_PYTHON_IMAGE" chown 10001:10001 /data
