## Build the connection between the services

The API’s `/healthz` works, but `/dependency` cannot reach its peer by name.
The application files and both containers are already supplied.

1. Create `$DOCKYARD_NETWORK` with the lab ownership label.
2. Attach the API and `$DOCKYARD_CONTAINER-dependency` to it.
3. Give the dependency the network alias `dependency`.
4. Test name lookup from the API container, then request the API’s `/dependency` route.
5. Leave both containers connected and running for Check work.

Keep the dependency unpublished: do not add a host port to it.
Use its name instead of hard-coding an IP address, and leave the supplied application code unchanged.
Explain what a successful name lookup would prove, and what the HTTP request proves in addition.
