## Service-to-service traffic has a different path

An API calling a dependency should not have to leave its Docker network through a host-published port.
Containers attached to the same user-defined bridge can communicate through their container interfaces.
Docker supplies name resolution on user-defined bridges, so a network-scoped alias can identify the dependency.

An IP address is an observation of a particular network endpoint.
It can change when a container is replaced.
A stable alias expresses the relationship the application intends: connect to the service named dependency.
The alias is scoped to the attached network, so a name on one bridge does not automatically resolve for a container on another bridge.

## Worked example: attach an existing service

```sh
docker network create --label "io.dockyard.lab=$DOCKYARD_LAB" "$DOCKYARD_NETWORK"
docker network connect --alias reports "$DOCKYARD_NETWORK" "$DOCKYARD_CONTAINER-dependency"
docker network inspect "$DOCKYARD_NETWORK"
```

The example attaches the dependency using the alias reports.
The task requires the alias dependency because that is the name the supplied API is configured to call.
Connecting only one container is insufficient: both sides need a route on the same intended bridge.

## DNS is only one observation

A successful name lookup proves that a name can resolve.
It does not prove the target port accepts connections or the application responds correctly.
Use both a lookup and a real dependency request.
The supplied API exposes `/dependency` to make that request from inside its container and report the dependency's observed identity.

## Publication is optional for internal services

A dependency does not need a host-published port for another container on its bridge to reach it.
Publishing every internal service adds exposure and extra host-port coordination without creating the service relationship.
In this lab only the API is published; the dependency remains internal.
