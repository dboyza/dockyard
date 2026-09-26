## A service is a role, not one fixed container

The worker role can have several replicas because each instance runs the same command and uses shared database and queue endpoints.
Compose can create those instances with `--scale worker=2`.
A fixed container_name prevents ordinary scaling because multiple containers cannot own the same name.
Let Compose name the workers, while retaining the lab ownership label on every replica.

The supplied workers claim queued database rows with transactional locking and skip rows already locked by another worker.
This prevents two active replicas from performing the same local job concurrently.
Real systems with external effects still need an explicit idempotency and delivery design; multiple replicas alone do not establish exactly-once behavior.

## Worked example: change a replica count

```sh
docker compose up -d --scale worker=2
docker compose ps worker
docker compose logs --tail 20 worker
```

The worker identity stored with a completed job lets you correlate its result with a real running worker.
Two running containers alone do not prove the application can use them; a submitted job must still complete.
The checker does not require a particular replica to win a race for a particular job.

## Profiles express optional roles

A service with `profiles: [tools]` is not started by a plain up unless that profile or service is selected.
This is useful for one-off diagnostics that should not become always-running application dependencies.
The supplied inspect service resolves the database service name from the same application network.

```sh
docker compose --profile tools run --rm inspect
```

Its printed address is a live observation, not a value to copy into application configuration.
The service can be invoked when needed and removed afterward without changing the durable application stack.

## Scale only the role designed for it

Increasing worker replicas is different from cloning a database with a shared writable data directory.
Each stateful service needs its own replication and storage design.
This task scales only the supplied stateless worker role and leaves one API, PostgreSQL instance, and Redis server.
