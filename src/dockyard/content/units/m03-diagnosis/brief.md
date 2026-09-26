## Repair one wrong address

Both services are already attached to the correct bridge and the dependency alias resolves.
The API is configured with `UPSTREAM_URL=http://127.0.0.1:8081/healthz`, which does not identify the peer service.
Diagnose this from inside the API container, then replace only the API with a corrected dependency URL.

The API must call `http://dependency:8080/healthz` on `$DOCKYARD_NETWORK`.
Keep the dependency unpublished and preserve its container.
Verify the actual peer identity appears in the API's successful `/dependency` response.
