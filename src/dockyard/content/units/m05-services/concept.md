## Describe all of Dispatch in one file

So far you have started containers one at a time.
**Docker Compose** reads a YAML file describing related services, their settings, networks, and storage, then starts them together.
A service is a role such as API or worker; a container is one running instance of that role.

Dispatch now has four roles:

- `api` accepts jobs and serves the dashboard you open in your browser.
- `db` runs PostgreSQL, a database server that keeps the jobs and their results.
- `queue` runs Redis, which sends notifications that work is available.
- `worker` takes queued jobs, processes their titles, and stores the results in PostgreSQL.

PostgreSQL keeps the actual list of unfinished jobs.
Workers also check that list periodically, so a lost Redis notification does not lose the job itself.
The Python code is supplied; your job is to connect and run these roles.

## Begin with the API

Create `compose.yaml` in the workspace.
This is a starting fragment; add the other roles before starting it:

```yaml
services:
  api:
    build:
      context: .
      args:
        BASE_IMAGE: ${DOCKYARD_PYTHON_IMAGE}
    image: ${DOCKYARD_IMAGE}
    container_name: ${DOCKYARD_CONTAINER}
    labels:
      io.dockyard.lab: ${DOCKYARD_LAB}
    environment:
      DB_HOST: db
      DB_NAME: dispatch
      DB_USER: dispatch
      DB_PASSWORD: ${DOCKYARD_DB_PASSWORD}
      REDIS_URL: redis://queue:6379/0
    ports:
      - "127.0.0.1:${DOCKYARD_PORT}:8080"
    networks: [app]
```

Indentation groups each setting under its parent; use spaces, not tabs.
The image’s default command starts `python app.py`.
The worker uses the same build, image, labels, environment, and network, with `command: [python, worker.py]`.
Give the worker no published port and no `container_name`, so Compose can create several copies later.

## Add the database, queue, and shared resources

For `db`, use `${DOCKYARD_POSTGRES_IMAGE}`, container name `${DOCKYARD_PROJECT}-db`, and these environment settings:

```yaml
environment:
  POSTGRES_DB: dispatch
  POSTGRES_USER: dispatch
  POSTGRES_PASSWORD: ${DOCKYARD_DB_PASSWORD}
volumes:
  - jobs:/var/lib/postgresql/data
```

For `queue`, use `${DOCKYARD_REDIS_IMAGE}` and container name `${DOCKYARD_PROJECT}-queue`.
Attach both services to `app` and give each the same lab label as the API.
They need no host ports: Compose lets the application reach them by their service names, `db` and `queue`, on the shared network.

Add these declarations at the top level, aligned with `services`:

```yaml
networks:
  app:
    name: ${DOCKYARD_NETWORK}
    labels:
      io.dockyard.lab: ${DOCKYARD_LAB}
volumes:
  jobs:
    name: ${DOCKYARD_VOLUME}
    labels:
      io.dockyard.lab: ${DOCKYARD_LAB}
```

The short names `app` and `jobs` connect service entries to these declarations.
The `name` settings choose the actual Docker resource names assigned to this lab.
Mount the PostgreSQL volume only into `db`, not into the API or workers.

## Understand where settings go

Compose replaces `${VARIABLE}` with a value from your terminal while reading the file.
This is called **interpolation**.
Only values listed under a service’s `environment` are then passed into that container.
A variable in your terminal is not automatically given to every service.

Dockyard also sets `COMPOSE_PROJECT_NAME` so commands in this lab address its own project.
Keep all commands in the lab terminal and workspace.
Check your model and start it:

```sh
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail 30
```

`config --quiet` validates the file without printing the resolved practice password.
A plain `config` can help inspect settings, but its output can include credentials.
Database initialization takes time; the next lesson teaches Compose how to wait for readiness.

## Follow a real job

Print your dashboard address with `printf 'http://127.0.0.1:%s\n' "$DOCKYARD_PORT"` and open it in your browser.
Submit a job and wait for its completed result.
Use the service logs to follow a failure: an API response alone does not prove the worker can finish the job.

`docker compose down` removes this project’s containers and network but normally preserves named volumes.
Adding `--volumes` deletes those volumes too, including their data.
For an ordinary stop that preserves the containers, use `docker compose stop`; use `docker compose start` to resume them.
