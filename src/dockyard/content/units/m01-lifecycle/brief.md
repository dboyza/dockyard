## Bring the prepared instance online

Prepare creates Dispatch's container but deliberately leaves its process unstarted.
The application source and port configuration are already supplied.

1. Use `docker ps -a` and `docker inspect` to identify the assigned container's state, ID, configured command, and host port.
2. Start that existing instance and make an HTTP request to `/healthz` through `127.0.0.1:$DOCKYARD_PORT`.
3. Stop and start it once more, comparing its ID before and after.
4. Leave it running and check your work.

The checker verifies current behavior, ownership, and the assigned endpoint.
Your observation about unchanged identity is a self-review question, not a claim that Dockyard recorded your command history.
