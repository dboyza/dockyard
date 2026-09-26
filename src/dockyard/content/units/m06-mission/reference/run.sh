#!/bin/sh
set -eu
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE" .
registry="127.0.0.1:$DOCKYARD_REGISTRY_PORT"
target="$registry/dispatch:release"
docker tag "$DOCKYARD_IMAGE" "$target"
docker push "$target"
release=$(docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$target" | python -c 'import sys; prefix=sys.argv[1]+"@"; print(next(line.strip() for line in sys.stdin if line.startswith(prefix)))' "$registry/dispatch")
docker pull "$release"
printf 'DISPATCH_RELEASE=%s\n' "$release" > .env
docker compose up -d --scale worker=2 --wait --wait-timeout 90
# Logical backup and restore do not assume raw live PostgreSQL files are portable.
docker exec "$DOCKYARD_PROJECT-db" pg_dump -U dispatch -d dispatch -Fc > dispatch.dump
docker exec "$DOCKYARD_PROJECT-db" createdb -U dispatch restored
docker exec -i "$DOCKYARD_PROJECT-db" pg_restore -U dispatch -d restored --exit-on-error < dispatch.dump
