## Create the internal service path

Prepare starts the API and a dependency container separately.
The API's normal `/healthz` endpoint works, but `/dependency` cannot reach the dependency by name.

Create `$DOCKYARD_NETWORK` with label `io.dockyard.lab=$DOCKYARD_LAB`.
Attach both assigned containers to it and give `$DOCKYARD_CONTAINER-dependency` the alias `dependency`.
Do not publish a host port for the dependency.
Do not replace the supplied application source or hard-code the dependency's current IP.

Verify `dependency` resolves from the API container and `/dependency` returns a successful response from that actual peer.
