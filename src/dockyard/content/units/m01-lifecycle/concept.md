## One container, several process lifetimes

`docker create` allocates a container and its configuration without starting its process.
`docker start` starts that existing container; `docker run` combines creation and startup.
A stopped container still has an identity, configuration, and writable layer.
Removing it with `docker rm` removes that container, while its reusable image remains.

A name is a convenient alias; the long container ID identifies a particular instance.
Starting a named instance retains that ID.
Removing and running another instance with the same name produces a different ID.
This distinction becomes important when you investigate stale logs or unexpectedly lost files.

## Read the evidence at the right level

`docker ps` lists running containers by default.
Use `docker ps -a` when a process has exited or has not started.
Inspect returns structured facts even when the process is stopped.

```sh
docker inspect --format '{{.State.Status}}' "$DOCKYARD_CONTAINER"
docker inspect --format '{{.Config.Image}} {{json .Config.Cmd}}' "$DOCKYARD_CONTAINER"
docker inspect --format '{{json .HostConfig.PortBindings}}' "$DOCKYARD_CONTAINER"
```

The first command answers a lifecycle question, the second answers what Docker will execute, and the third answers how a host request should reach it.
Do not infer an HTTP endpoint from a container name.

## Worked example: restarting a known instance

```sh
docker stop "$DOCKYARD_CONTAINER"
docker start "$DOCKYARD_CONTAINER"
docker ps --filter "id=$DOCKYARD_CONTAINER"
```

Use the sequence on a running practice instance, then compare its ID before and after.
A restart is useful when process state must be replaced without changing the container's configuration.
To change a port binding or an environment variable, create a replacement container instead.

## Boundaries on this Mac

Docker Desktop runs Linux containers inside its Linux VM.
The process ID reported by inspection belongs to that VM's host namespace, not directly to macOS.
Use Docker's inspection and exec tools to investigate it; do not send a macOS signal to that numeric PID.
