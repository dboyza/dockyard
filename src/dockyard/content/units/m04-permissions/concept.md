## The API is alive, but cannot save a job

This lab’s API can answer `/healthz`, yet writing a job fails.
Its database directory is on a named volume whose owner does not match the application’s user.
You will repair the directory’s ownership while keeping the API running as an ordinary user.

## Compare the process with the directory

First try a real write, then inspect both identities:

```sh
curl -H 'Content-Type: application/json' -d '{"title":"permission check"}' \
  "http://127.0.0.1:$DOCKYARD_PORT/jobs"
docker exec "$DOCKYARD_CONTAINER" id
docker exec "$DOCKYARD_CONTAINER" ls -ldn /data
docker logs --tail 20 "$DOCKYARD_CONTAINER"
```

`id` shows the process user ID (UID) and group ID (GID).
Here both are 10001.
In `ls -ldn`, `-d` inspects the directory itself and `-n` shows numeric owners.
The prepared directory belongs to root, number 0, and has mode `0700`.
That mode allows only its owner to read, write, or enter it.

Linux uses these numbers to decide access; matching friendly user names is not enough.
Rebuilding the image does not change the owner already stored on a separate volume.

```figure
ownership-mismatch
```

## Repair the identified directory

Use a temporary maintenance container to change just this volume’s directory owner:

```sh
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -v "$DOCKYARD_VOLUME:/data" "$DOCKYARD_PYTHON_IMAGE" \
  chown 10001:10001 /data
```

This temporary container runs with permission to make the ownership change.
`--rm` removes it when the command finishes; the named volume remains.
The ordinary API continues to run as user 10001.

Repeat the directory inspection and job request.
The owner should now match the API, and the write should succeed.
Making the directory writable by everyone with `chmod 777`, or running the API as root, would avoid the mismatch by giving broader access than this job needs.

A successful health request alone cannot demonstrate this repair.
Always repeat the operation that was failing for the user.
