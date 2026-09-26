#!/bin/sh
set -eu
curl --retry 10 --retry-connrefused --retry-delay 1 --fail "http://127.0.0.1:$DOCKYARD_PORT/healthz"
docker stop "$DOCKYARD_CONTAINER"
