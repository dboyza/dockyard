## Persist jobs through a host bind

Build the supplied checkpoint as `$DOCKYARD_IMAGE`.
Create `$DOCKYARD_STORAGE` and mount it read-write at `/data` in the assigned API container.
Use your host UID/GID for this bind-mounted exercise, and preserve the usual label and loopback port contract.

Create a job with `curl -H 'Content-Type: application/json' -d '{"title":"First durable job"}' "http://127.0.0.1:$DOCKYARD_PORT/jobs"`.
Read `/jobs`, replace the assigned container using the same data mount, and confirm your job remains.
Leave the replacement running.
The checker verifies the mount and real durable writes; your replacement sequence is part of the self-review observation.
