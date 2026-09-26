#!/bin/sh
set -eu
docker exec --user 0 "$DOCKYARD_CONTAINER" chmod 600 /data/jobs.db
