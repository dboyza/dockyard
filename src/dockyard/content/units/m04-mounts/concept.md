## Four different places a file can live

An image carries read-only layers shared by containers.
Each container also has a writable layer that belongs to that particular container.
Removing the container removes that writable layer.
A mount at `/data` redirects accesses at that path to storage with a separate lifecycle.

A bind mount exposes a specific host path.
It is useful when the operator needs direct access to source or data on the host, but ties the runtime to that path and its permissions.
A named volume is managed by Docker and is usually a better fit for service data that does not need direct host editing.
Both can outlive container replacement; neither is automatically a backup.

## A mount hides the covered directory

Mounting a directory over `/app` changes what the process sees at `/app`.
The original image files are not merged with arbitrary bind-mounted files.
For this checkpoint the application lives in `/app` and its SQLite database belongs in `/data`.
Mount the data path without hiding the packaged application.

## Worked example: an explicit bind mount

```sh
mkdir -p "$DOCKYARD_STORAGE"
```

A run command can then use `--mount "type=bind,source=$DOCKYARD_STORAGE,target=/data"`.
The more explicit --mount form reports a missing host source path instead of quietly selecting an unintended location.
In this lab the data directory sits beside the source workspace, so runtime database writes do not appear as source edits during assessment.

## Permissions cross the boundary too

The host directory and container process have numeric owners.
For this host-bind exercise, run the API as your host UID and GID using `--user "$(id -u):$(id -g)"` so it can write its own practice directory.
The supplied image makes application files readable to that identity.
The following lab treats ownership inside a Docker-managed volume separately.

## Verify data rather than names

POSTing a job proves the application can write, and reading it through a separate container proves the committed database is accessible through the mount.
The checker creates a uniquely named observation job, confirms it independently, and removes only that observation afterward.
Your own jobs remain intact.
