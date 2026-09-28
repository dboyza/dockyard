## Publish a release and run it by digest

Dockyard has built a working Dispatch image as `$DOCKYARD_IMAGE` and started this lab’s registry.

1. Tag the image as `127.0.0.1:$DOCKYARD_REGISTRY_PORT/dispatch:release` and push it.
2. Find the digest this registry reported for it.
3. Pull the image by digest, then run `$DOCKYARD_CONTAINER` from that digest reference, with the lab label and `127.0.0.1:$DOCKYARD_PORT:8080`.
4. Check that `/healthz` reports release `dispatch-1`.

Leave both the registry and the API running, then choose **Check work**.
