## Start Dispatch and complete a job

Write a Compose project with `api`, `db`, `queue`, and at least two `worker` replicas.
Use the supplied pinned images and application build settings.
Keep the assigned container names for API, database, and queue, and let Compose name the workers.

Label every service, the assigned network `$DOCKYARD_NETWORK`, and PostgreSQL volume `$DOCKYARD_VOLUME` with the lab identity.
Mount the volume into PostgreSQL at `/var/lib/postgresql/data`.
Use the database and Redis settings taught in this module, and publish only the API at `127.0.0.1:${DOCKYARD_PORT}:8080`.

Give API, PostgreSQL, and Redis useful health checks.
Make API and worker wait for healthy database and queue services.
Start the project and demonstrate that a new job finishes and its result is stored in PostgreSQL.

Write down how to start, inspect, stop, and resume this project while preserving its data.
Leave it running for the checker.
