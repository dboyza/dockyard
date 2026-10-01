## Wait until a dependency can do its job

A container can be running while its database is still starting.
This lab’s Compose file starts containers in order, but does not wait for the database or queue to answer requests.
You will add **health checks**, commands Docker runs periodically inside a container to test whether it is ready.

A health command succeeds with exit status 0 and fails with a nonzero status.
It must test useful work, not just print a success message.
Inside a health check, localhost refers to that service’s own container.

## Check PostgreSQL and Redis

Add this under the `db` service:

```yaml
healthcheck:
  test: [CMD-SHELL, "pg_isready -U dispatch -d dispatch"]
  interval: 2s
  timeout: 3s
  retries: 20
  start_period: 5s
```

`pg_isready` asks whether PostgreSQL accepts connections.
Docker runs it every two seconds, allows three seconds per attempt, and marks repeated failures unhealthy.
The start period allows initial setup before counting failures toward that limit.

Under `queue`, use the same timing settings with `test: [CMD, redis-cli, ping]`.
Redis should answer `PONG`.

## Make startup depend on those checks

Add this under both `api` and `worker`, replacing their existing `depends_on` entries:

```yaml
depends_on:
  db:
    condition: service_healthy
  queue:
    condition: service_healthy
```

`service_started` waits for a running container.
`service_healthy` waits for its health check to succeed.
You need both the dependency’s health check and this condition.

```figure
health-wait
```

Give the API its own health check as well:

```yaml
healthcheck:
  test: [CMD, python, -c, "from urllib.request import urlopen; urlopen('http://127.0.0.1:8080/readyz', timeout=2)"]
  interval: 2s
  timeout: 3s
  retries: 20
```

Dispatch’s `/readyz` tests its database and Redis access.
Its `/healthz` only tells you the HTTP process is alive.
The Python command is used because Python is already in the image; you do not need to install curl inside it.

## Apply, wait, and inspect

```sh
docker compose config --quiet
docker compose up --wait --wait-timeout 90
docker compose ps
```

The wait ends successfully when the services are ready, or fails after the deadline.
If it fails, inspect the relevant service’s logs and health output, for example:

```sh
docker inspect --format '{{json .State.Health}}' "$DOCKYARD_PROJECT-db"
```

Then submit a job and wait for its result.
Startup checks do not guarantee dependencies remain available forever; applications still need to handle failures after startup.
The supplied worker retries and leaves unfinished jobs in PostgreSQL for later processing.
