## The caller decides what localhost means

A request made from your host computer and a request made from inside Dispatch begin in different network namespaces.
The same string, `127.0.0.1`, refers to a different loopback interface in each.
If the API uses a loopback URL for its dependency, it calls itself or another listener inside its own container.
It does not call a neighboring container merely because both run on the same host computer.

## Separate the diagnostic layers

First inspect the API's configured dependency URL.
Then test name resolution from inside that API container.
Next test the target port and application response.
A DNS success with a connection refusal suggests a different problem from a name that does not resolve at all.

```sh
docker inspect --format '{{json .Config.Env}}' "$DOCKYARD_CONTAINER"
docker exec "$DOCKYARD_CONTAINER" python -c 'import socket; print(socket.gethostbyname("dependency"))'
docker exec "$DOCKYARD_CONTAINER" python -c 'from urllib.request import urlopen; print(urlopen("http://dependency:8080/healthz", timeout=2).read().decode())'
```

These commands observe the same caller-side environment as the API.
Using curl on the host can verify publication but cannot, by itself, prove the API's internal dependency route.
The supplied application reports its dependency result at `/dependency` so you can correlate both views.

## Worked example: classify two symptoms

A hostname lookup error points toward the name, alias, or network attachment.
A resolved address followed by connection refusal points toward the port or listener.
An HTTP error proves that something accepted the connection and answered at the application layer, although it may still be the wrong service.
Preserve these distinctions in your diagnosis instead of calling every failure a network outage.

## Configuration replacement

The dependency URL is an environment variable recorded when the container is created.
Changing a shell variable on your host computer does not alter an existing container's environment.
Create a corrected replacement while keeping the assigned label, bridge, and publication contract.
