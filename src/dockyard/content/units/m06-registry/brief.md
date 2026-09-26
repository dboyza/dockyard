## Publish and select a release

Prepare builds the known-good application image and starts the assigned local registry.
Tag the application as `127.0.0.1:$DOCKYARD_REGISTRY_PORT/dispatch:release`, push it, and find its digest in that repository.
Pull that digest, then create the assigned API container using the digest reference rather than the mutable tag.
Keep the usual lab label and loopback API port contract.

Leave the registry and API running.
Verify the API reports release `dispatch-1`, and explain why its Config.Image reference includes @sha256.
