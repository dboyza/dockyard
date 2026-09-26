## A project describes related resources

Compose reads a YAML application model and creates its services, networks, and volumes under a project identity.
A service describes a role; its container is an instance of that role.
The same file can create a new isolated project when the project name and resource names are scoped appropriately.
Dockyard supplies COMPOSE_PROJECT_NAME so commands in the lab shell address this practice project.

The supplied Dispatch checkpoint now has four roles.
The API accepts jobs and serves a small dashboard, PostgreSQL stores durable job state, Redis carries notifications, and workers complete jobs.
The database remains the source of queued work, so workers can recover a lost notification by polling durable rows.
This is an educational local workflow, not a claim of exactly-once processing across arbitrary external side effects.

## Worked example: model a small web/cache pair

```yaml
services:
  web:
    build: .
    environment:
      CACHE_HOST: cache
    ports:
      - "127.0.0.1:49152:8080"
  cache:
    image: your-pinned-cache-image
```

Compose gives services on their project network discoverable service names.
The cache does not need a published host port for the web service to reach it.
The task expands this idea to Dispatch's four real roles and an explicit labeled network.

## Interpolation and container environment differ

`${VARIABLE}` is expanded by Compose while reading the model, using the host environment and applicable environment files.
A service's `environment` section then chooses what values are passed into that container.
Exporting a shell variable does not automatically inject it into every service.
Use `docker compose config` to inspect the resolved model before creating resources, but remember that resolved output may contain this lab's practice credentials.
Do not paste credentials into notes or exports.

## Shared application settings

API and worker use the same built image but different commands.
The API runs `python app.py`; workers run `python worker.py`.
They both need DB_HOST=db, DB_NAME=dispatch, DB_USER=dispatch, DB_PASSWORD from DOCKYARD_DB_PASSWORD, and REDIS_URL=redis://queue:6379/0.
PostgreSQL receives corresponding POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD values.
The dependency image variables are already pinned by the lab environment.

YAML anchors such as `&application` and aliases such as `*application` can share repeated mappings.
The supplied later checkpoint uses them to keep API and worker settings consistent.
Plain repeated mappings are equally valid when they meet the same contract.

## Start, inspect, and stop with scope

`docker compose up -d --build` builds the application and starts its services.
`docker compose ps` and `docker compose logs --tail 30` inspect this project.
`docker compose down` removes its containers and network but ordinarily retains named volumes; adding `--volumes` removes those volumes too.
Use that destructive option only when intentionally resetting the assigned practice data.
