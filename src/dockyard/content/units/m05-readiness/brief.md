## Make the startup wait meaningful

Add working health checks for PostgreSQL, Redis, and the API’s `/readyz` endpoint.
Make both API and worker depend on healthy database and queue services.
Validate the Compose file, apply it, and wait with a 90-second deadline.

Check that the three health checks are healthy and a newly submitted job finishes.
An unconditional success command does not demonstrate readiness.
Explain why the API’s `/healthz` is not enough for this task.
