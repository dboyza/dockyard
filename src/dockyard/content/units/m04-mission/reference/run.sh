#!/bin/sh
set -eu
# Stop the source process so the SQLite file is quiescent before copying it.
docker stop "$DOCKYARD_CONTAINER"
docker cp "$DOCKYARD_CONTAINER:/data/jobs.db" ./jobs.db
tar -cf backup.tar jobs.db
docker volume create --label "io.dockyard.lab=$DOCKYARD_LAB" "$DOCKYARD_VOLUME"
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -v "$DOCKYARD_VOLUME:/data" -v "$DOCKYARD_WORKSPACE:/backup:ro" \
  "$DOCKYARD_PYTHON_IMAGE" sh -c 'tar -xf /backup/backup.tar -C /data && chown -R 10001:10001 /data'
docker rm "$DOCKYARD_CONTAINER"
docker run -d --name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" -v "$DOCKYARD_VOLUME:/data" "$DOCKYARD_IMAGE"
