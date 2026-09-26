#!/bin/sh
set -eu
registry="127.0.0.1:$DOCKYARD_REGISTRY_PORT"
target="$registry/dispatch:release"
docker tag "$DOCKYARD_IMAGE" "$target"
docker push "$target"
release=$(docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$target" | python -c 'import sys; prefix=sys.argv[1]+"@"; print(next(line.strip() for line in sys.stdin if line.startswith(prefix)))' "$registry/dispatch")
docker pull "$release"
docker run -d --name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB" -p "127.0.0.1:$DOCKYARD_PORT:8080" "$release"
