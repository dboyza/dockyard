## Fix the port mapping

The prepared container runs a working Dispatch image, but its host port points to the wrong port inside the container.

1. Inspect the process, recent logs, and published port mapping.
2. Write down which side of the mapping disagrees with the application’s listener.
3. Replace only the assigned container with a mapping from `127.0.0.1:$DOCKYARD_PORT` to port 8080 inside it.
4. Keep the lab label and supplied image, without a workspace mount.
5. Check that `/healthz` returns `dispatch-1`, then check your work.

Explain why changing only the host port would not fix the original mismatch.
The checker verifies the resulting endpoint; it does not grade that explanation.
