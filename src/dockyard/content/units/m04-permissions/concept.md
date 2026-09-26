## A healthy listener can hide a broken workflow

The supplied `/healthz` endpoint establishes that the HTTP process is alive.
Creating a job exercises the persistence path.
A service can answer health requests while a job write fails because its mounted data directory has the wrong owner.
Probe the operation users actually need before declaring recovery.

## Numeric identities matter

Linux file access is decided using numeric UIDs, GIDs, permission bits, and applicable access controls.
A friendly user name is a lookup aid, not the authority itself.
This image runs its API as UID 10001 and GID 10001.
A volume directory owned by root with mode 0700 gives that application identity no access.

```sh
docker exec "$DOCKYARD_CONTAINER" id
docker exec "$DOCKYARD_CONTAINER" ls -ldn /data
docker logs --tail 20 "$DOCKYARD_CONTAINER"
```

Compare those observations with the actual POST /jobs response.
The volume mount takes precedence over the image directory, so correct ownership in the Dockerfile does not guarantee a previously created volume has matching ownership.

## Worked example: a narrow ownership repair

An operator can attach a short-lived maintenance container to the specific owned volume and change its directory ownership.
That maintenance action may run as root inside the container, while the ordinary API continues to run without root privileges.
The scope is the identified lab volume, not a host filesystem tree.

```sh
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -v "$DOCKYARD_VOLUME:/data" "$DOCKYARD_PYTHON_IMAGE" \
  chown 10001:10001 /data
```

Changing a single assigned directory is enough for this fixture.
Do not apply recursive ownership changes to unrelated paths.
Making a directory world-writable or switching the long-running API to root would broaden authority instead of aligning ownership with the application.

## Lifecycle reminder

A named volume survives normal container removal.
That is why it can retain an ownership error across repeated rebuilds and restarts.
Diagnose and repair the stored resource that actually carries the error.
