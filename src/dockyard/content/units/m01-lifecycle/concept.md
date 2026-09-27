## Stop the program, keep the container

In the last lesson, you stopped Dispatch and started it again.
Now let’s check what changed and what stayed the same.

`docker create` creates a container with its settings, but does not start its program.
`docker start` starts that existing container; `docker run` combines creation and startup.
A stopped container still has an identity, configuration, and writable layer.
Removing it with `docker rm` removes that container, while its reusable image remains.

A name is a convenient alias; the long container ID identifies a particular instance.
Starting a named instance retains that ID.
Removing and running another instance with the same name produces a different ID.
This distinction becomes important when you investigate stale logs or unexpectedly lost files.

## Find out what Docker has created

`docker ps` lists running containers by default.
Use `docker ps -a` when a process has exited or has not started.
Inspect returns structured facts even when the process is stopped.

```sh
docker inspect --format '{{.State.Status}}' "$DOCKYARD_CONTAINER"
docker inspect --format '{{.Config.Image}} {{json .Config.Cmd}}' "$DOCKYARD_CONTAINER"
docker inspect --format '{{json .HostConfig.PortBindings}}' "$DOCKYARD_CONTAINER"
```

`--format` selects the information you want from Docker’s inspection result.
The braces and field names are a template Docker reads, not words you need to replace.
The first command shows whether the container is created, running, or exited.
The second shows its image and launch command.
The third shows how ports on your computer connect to ports in the container.
Do not infer an HTTP endpoint from a container name.

## Worked example: restarting a known instance

```sh
docker stop "$DOCKYARD_CONTAINER"
docker start "$DOCKYARD_CONTAINER"
docker ps --filter "name=$DOCKYARD_CONTAINER"
```

In this lab the prepared container has not been started yet, so start it once before trying this sequence.
Run `docker inspect --format '{{.Id}}' "$DOCKYARD_CONTAINER"` before and after the stop/start.
The IDs should match.
The `name` filter uses the assigned container name; an `id` filter would need its actual ID.
If the first health request fails just after startup, wait a moment and try again.
A restart is useful when process state must be replaced without changing the container's configuration.
To change a port binding or an environment variable, create a replacement container instead.

## Boundaries on the host

Docker Desktop runs Linux containers in a Linux environment on macOS and Windows.
A native Linux Docker Engine runs them on its host kernel.
The process ID reported by inspection belongs to the Docker daemon's host namespace, which may be inside a VM.
Use Docker's inspection, exec, and stop tools to investigate and control the assigned container rather than sending a host signal to that numeric PID.
