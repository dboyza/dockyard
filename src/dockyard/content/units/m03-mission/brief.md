## Connectivity contract

Build the supplied checkpoint as `$DOCKYARD_IMAGE`.
Create a labeled bridge named `$DOCKYARD_NETWORK`.
Run the API as `$DOCKYARD_CONTAINER` and the internal service as `$DOCKYARD_CONTAINER-dependency`, labeling both with the assigned lab ID.
Attach both to that bridge and give the peer the alias `dependency`.
Only the API may publish a host port, at `127.0.0.1:$DOCKYARD_PORT:8080`.
The API must use `http://dependency:8080/healthz` as its upstream URL.

Leave both processes running.
Prove the host can reach the API, the API can resolve the peer, and the API's dependency response identifies that peer.
Record where a host-port conflict and a DNS failure would appear along this path.
