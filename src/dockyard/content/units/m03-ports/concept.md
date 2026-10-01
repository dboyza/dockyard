## Follow a request from your computer to Dispatch

Dispatch can be running correctly while Docker forwards requests to the wrong port.
In this lesson you’ll inspect that mismatch and repair only the mapping.
The supplied application listens on port 8080 inside its container.

Read a mapping such as `127.0.0.1:49152:8080` from left to right:

- `127.0.0.1` is the address on your computer where Docker accepts requests.
- `49152` is the port on your computer.
- `8080` is the destination port inside the container.

The mapping forwards traffic; it does not change the port the application listens on.
For example, forwarding to 8081 would be wrong for this application even if the host port were correct.

```figure
port-mapping-mismatch
```

## Inspect before replacing

Prepare the lab, open its terminal, and run:

```sh
docker ps --filter "name=$DOCKYARD_CONTAINER"
docker logs --tail 20 "$DOCKYARD_CONTAINER"
docker port "$DOCKYARD_CONTAINER"
curl --max-time 3 "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

The logs should say Dispatch listens on `0.0.0.0:8080`.
Compare that with the container port shown by `docker port`.
A request can fail here even though the container is running, because the forwarding rule sends it somewhere the app is not listening.
`--max-time 3` stops curl waiting after three seconds.

You cannot change an existing container’s published port mapping in place.
After recording the wrong mapping, stop and remove only the assigned container, then create its replacement:

```sh
docker stop "$DOCKYARD_CONTAINER"
docker rm "$DOCKYARD_CONTAINER"
docker run -d --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" "$DOCKYARD_IMAGE"
```

The image is already built, so you do not need to rebuild or mount the application source.
Repeat the port inspection and health request after the app starts.

## Localhost depends on where you stand

`127.0.0.1` refers to the environment making the request.
In your lab terminal it refers to the host environment; on Windows, that terminal runs in WSL.
Inside a container, it refers to that container’s own network environment, not your computer or a neighboring container.

The server listens on `0.0.0.0` inside the container so it can receive forwarded traffic through its container interface.
On the host side, we deliberately publish only to `127.0.0.1` for local practice.
Those addresses serve different purposes.

```figure
localhost-perspective
```

Use the published host endpoint for requests from your computer.
A container’s private IP is not the portable host-access method across Docker Desktop and native Linux.
The next lesson uses a Docker network for requests between containers.
