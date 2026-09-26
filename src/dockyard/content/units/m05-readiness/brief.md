## Make startup assumptions explicit

Prepare starts a stack that may work after initialization but has no health checks and only service_started dependency conditions.
Add PostgreSQL and Redis health checks, an API `/readyz` health check, and service_healthy guards for both API and worker dependencies.

Apply the model and use a bounded `docker compose up --wait` to establish readiness.
Verify all three health checks are healthy and a new job is processed and stored.
Do not replace the real health checks with unconditional success commands.
