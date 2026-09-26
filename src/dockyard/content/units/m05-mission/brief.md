## Application delivery contract

Create a complete Compose project with API, PostgreSQL, Redis, and at least two workers.
Use the supplied pinned images and application build, the assigned names for API/db/queue, the labeled `$DOCKYARD_NETWORK`, and PostgreSQL volume `$DOCKYARD_VOLUME`.
Apply the environment configuration from this module and publish only the API on the assigned loopback endpoint.

Give API, PostgreSQL, and Redis meaningful health checks.
Make API and worker wait for healthy database and queue dependencies.
Use scalable worker identities.
Leave the complete application healthy and demonstrate a newly submitted job reaches a completed result in PostgreSQL.
Record how to start, inspect, stop, and resume the project while preserving its data.
