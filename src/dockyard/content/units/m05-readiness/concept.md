## Started is not ready

A database container can be running while initializing its files or creating its first database.
Starting the API after the database container exists does not necessarily mean the database accepts connections.
Compose can wait for a declared health check when a dependency uses condition `service_healthy`.
That requires both a meaningful health check and the dependency condition.

A health check runs inside the checked service's container.
Its localhost refers to that container.
The command must exist in the image and return a useful exit status.
A check that always returns zero, or only proves a binary exists, does not establish readiness.

## Worked example: a database readiness gate

```yaml
healthcheck:
  test: [CMD-SHELL, "pg_isready -U dispatch -d dispatch"]
  interval: 2s
  timeout: 3s
  retries: 20
```

An API dependency can then specify `db: {condition: service_healthy}` under depends_on.
For Redis, `redis-cli ping` checks that the server answers.
The API's `/readyz` checks both its database access and queue availability; `/healthz` only reports process liveness.

## Readiness must tolerate time

A short start period can accommodate known initialization work without treating each early failure as permanent.
Retries and deadlines should be long enough for the expected operation and bounded enough to expose a genuine fault.
`docker compose up --wait --wait-timeout 90` gives this local workflow a visible bounded readiness wait.
When the wait fails, inspect the specific service's health output rather than merely increasing every timeout.

## Startup guards are not recovery logic

A healthy dependency can fail after the application starts.
Applications still need suitable connection handling, retries, and useful error reporting.
The supplied worker retries dependency failures and keeps durable queued rows in PostgreSQL.
The API reports unavailable dependencies instead of claiming every accepted request succeeded.

This lab checks real health states, the resolved dependency conditions, and a completed background job.
The configuration inspection alone is insufficient: the actual checks must be healthy and the workflow must work.
