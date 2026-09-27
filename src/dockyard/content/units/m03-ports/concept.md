## A request crosses an explicit mapping

The address your browser uses belongs to the host computer.
The address the application listens on belongs to its container's network namespace.
A mapping such as `127.0.0.1:49152:8080` connects the host computer's loopback port 49152 to container port 8080.
These port numbers may differ, and neither number changes the application's configured listener.

Docker Desktop carries the forwarded traffic through its Linux environment; native Linux Docker Engine publishes it on its host.
On this host computer, directly using a container's private bridge IP from the host is not the intended portable access path.
Use the published host endpoint for host-to-container requests.

## Worked example: read the mapping left to right

```sh
docker port "$DOCKYARD_CONTAINER"
docker inspect --format '{{json .NetworkSettings.Ports}}' "$DOCKYARD_CONTAINER"
```

For an application listening on container port 9000, `-p 127.0.0.1:49152:9000` would create the matching host route.
Publishing 49152 to container port 9001 would not make the application move to 9001.
It would forward requests to a port where that application is not listening.

## Two different loopbacks

`127.0.0.1` in your terminal refers to the host environment running that terminal.
On Windows, the lab terminal runs inside WSL 2, with Windows browser access handled by localhost forwarding.
Inside a container, that address refers to the container itself.
A server bound only to container loopback cannot normally receive packets forwarded to its container interface.
The supplied API listens on `0.0.0.0:8080` inside its container, accepting traffic to any of that namespace's interfaces.
The host side is deliberately restricted to `127.0.0.1` so the practice endpoint is not published to other machines.

## Diagnose in order

Establish whether the process is running, what address and port it reports, how Docker maps the host endpoint, and whether a real request succeeds.
A failed request alone does not identify which of these layers is wrong.
Changing every port at once removes useful evidence.
