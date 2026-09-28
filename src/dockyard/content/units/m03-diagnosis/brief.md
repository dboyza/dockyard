## Repair the API’s dependency address

The bridge and dependency alias already work.
The API has `UPSTREAM_URL=http://127.0.0.1:8081/healthz`, which points into the API’s own container.

1. Inspect that setting and test the dependency name and correct URL from inside the API container.
2. Replace only the API, setting its upstream URL to `http://dependency:8080/healthz`.
3. Keep its lab label, `$DOCKYARD_NETWORK` attachment, image, and local port mapping.
4. Request `/dependency` and confirm that it identifies the actual peer, then check your work.

Preserve the dependency container and keep it unpublished.
Explain why testing only with curl on your computer would miss part of this diagnosis.
