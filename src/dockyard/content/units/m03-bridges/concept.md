## Let two containers find each other

Dispatch now has a small HTTP dependency: another service it asks for a health response.
You’ll connect the two containers without publishing the dependency to your computer.
The API’s `/healthz` checks the API itself; its `/dependency` route asks the other service and reports what answered.

A **user-defined bridge network** is a Docker-managed network you create for related containers.
Containers attached to it can communicate, and Docker provides name lookup between them.
A **network alias** is an extra name for a container on that network.
The supplied API expects the name `dependency`.

```figure
bridge-network
```

## Connect both ends

Prepare creates the two containers, but their intended connection is missing.
Create the assigned network and attach both containers:

```sh
docker network create --label "io.dockyard.lab=$DOCKYARD_LAB" "$DOCKYARD_NETWORK"
docker network connect "$DOCKYARD_NETWORK" "$DOCKYARD_CONTAINER"
docker network connect --alias dependency "$DOCKYARD_NETWORK" "$DOCKYARD_CONTAINER-dependency"
docker network inspect "$DOCKYARD_NETWORK"
```

The final inspection should include both container names.
The `--alias` belongs on the dependency’s connection, because that is the name the API will look up.
Attaching only one container does not create a path between them.
If Docker says a network or connection already exists, inspect it before repeating the creation command.

## Test a name and a request

```sh
docker exec "$DOCKYARD_CONTAINER" python -c 'import socket; print(socket.gethostbyname("dependency"))'
curl --fail "http://127.0.0.1:$DOCKYARD_PORT/dependency"
```

The Python command runs inside the API container and asks DNS, the name-lookup system, for the dependency’s address.
You can run it as shown without writing application code.
The address is an observation, not a value to copy into configuration: it can change when the dependency is replaced.

The second command asks the API to make a real request to its dependency.
Name lookup alone would not tell us whether the target port or application works.
Look for a successful result identifying the actual dependency container.

## Keep internal services internal

The API has a published host port because your computer needs to call it.
The dependency needs no published port because the API reaches it over their Docker network.
Publishing every service would add host ports without solving a missing network connection or alias.
A name on one network also does not automatically work for a container attached only to another network.
