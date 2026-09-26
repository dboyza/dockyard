#!/bin/sh
set -eu
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -v "$DOCKYARD_VOLUME-source:/data:ro" -v "$DOCKYARD_WORKSPACE:/backup" \
  "$DOCKYARD_PYTHON_IMAGE" tar -cf /backup/backup.tar -C /data jobs.db
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -v "$DOCKYARD_VOLUME:/data" -v "$DOCKYARD_WORKSPACE:/backup:ro" \
  "$DOCKYARD_PYTHON_IMAGE" sh -c 'tar -xf /backup/backup.tar -C /data && chown -R 10001:10001 /data'
