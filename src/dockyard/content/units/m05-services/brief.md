## Assemble Dispatch

Write compose.yaml for services `api`, `worker`, `db`, and `queue` using the supplied Dockerfile and application sources.
Build API and worker as `$DOCKYARD_IMAGE`, passing the pinned Python BASE_IMAGE argument.
Use `$DOCKYARD_POSTGRES_IMAGE` and `$DOCKYARD_REDIS_IMAGE` for the dependencies.
Configure the database and queue addresses described in the lesson.

Name the API container `$DOCKYARD_CONTAINER`, the database `$DOCKYARD_PROJECT-db`, and the queue `$DOCKYARD_PROJECT-queue`.
Label every service, network, and volume with `io.dockyard.lab: ${DOCKYARD_LAB}`.
Use the network name `$DOCKYARD_NETWORK` and a PostgreSQL volume named `$DOCKYARD_VOLUME`, mounted at `/var/lib/postgresql/data`.
Only the API should publish `127.0.0.1:${DOCKYARD_PORT}:8080`.
Do not assign a fixed container_name to worker, because the next exercise scales it.

Start the stack, open the API dashboard at the assigned host port, and submit a job.
A complete result requires a worker to finish that job and store its real result in PostgreSQL.
Readiness guards are introduced in the next lab; the reference includes them as a useful complete implementation.
