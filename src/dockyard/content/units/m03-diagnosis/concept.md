## The address is valid, but it points to the wrong place

In this lab both containers are already connected correctly.
The API instead has a wrong `UPSTREAM_URL`, the setting telling it which dependency to call.
It uses `127.0.0.1`, so it looks inside its own container rather than at its neighbor.

A **network namespace** is a process’s separate view of network interfaces, addresses, and routes.
You have already used the practical consequence: localhost means the environment making the request.
To diagnose the API’s problem, test from the API container.

## Compare configuration, lookup, and response

```sh
docker inspect --format '{{json .Config.Env}}' "$DOCKYARD_CONTAINER"
docker exec "$DOCKYARD_CONTAINER" python -c 'import socket; print(socket.gethostbyname("dependency"))'
docker exec "$DOCKYARD_CONTAINER" python -c 'from urllib.request import urlopen; print(urlopen("http://dependency:8080/healthz", timeout=2).read().decode())'
```

Find `UPSTREAM_URL` in the first output.
This lab contains only practice settings, but inspecting a real container’s full environment can reveal credentials; do not copy that output into public notes.
The second command tests name lookup, and the third tests a request to the peer from the caller’s actual network environment.

Here, the name and correct peer URL should work even while the API’s configured URL fails.
A hostname error, a refused connection, and an HTTP error are different observations.
A refused connection means you reached an address but no listener accepted that port; an HTTP error means a service accepted the connection and replied.

## Change the container’s setting

Changing an environment variable in your terminal does not update an existing container.
Create a replacement with the corrected setting:

```sh
docker stop "$DOCKYARD_CONTAINER"
docker rm "$DOCKYARD_CONTAINER"
docker run -d --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  --network "$DOCKYARD_NETWORK" \
  -e UPSTREAM_URL=http://dependency:8080/healthz \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" "$DOCKYARD_IMAGE"
```

`-e` passes the setting into the new container.
`--network` attaches it to the existing lab network when it is created.
Do not replace the dependency or publish its port.

Once the replacement has started, request `/dependency` through the assigned host port.
Its result should identify the real peer, not just contain a generic success message.
