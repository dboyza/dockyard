## Run two workers for the same queue

The prepared stack has one worker.
You will add a second and observe real completed jobs.
A **replica** is another instance of the same service role.
Each worker uses the same application image and shared database and queue settings.

```sh
docker compose up -d --scale worker=2
docker compose ps worker
docker compose logs --tail 20 worker
```

There should now be two running worker containers.
A fixed `container_name` would prevent this because two containers cannot have the same name.
Let Compose choose their names and keep the lab label on both.

The supplied worker claims a job in a database transaction and skips rows another worker has already locked.
That prevents these workers from handling the same local job at the same time.

```figure
worker-replicas
```
It does not guarantee that arbitrary external actions, such as charging a payment, happen exactly once.
Such applications need additional protection against repeated actions.

## Follow the workers’ results

Submit several jobs through the dashboard and inspect the worker identity stored with each completed result.
One worker may win several jobs in a row; equal distribution is not promised.
The checker requires the worker count and a real completed result, not a particular worker winning a race.

The prepared file also includes an optional diagnostic service:

```sh
docker compose --profile tools run --rm inspect
```

A **profile** groups services that start only when selected.
Here `tools` includes a short-lived container that resolves the database’s service name on the application network.
Its printed address is an observation, not an address to hard-code into the app.

## Practice a database backup before the capstone

SQLite used a closed file in the previous module.
PostgreSQL is a running database server, so use its own `pg_dump` tool to make a consistent logical backup: a file of SQL instructions that recreate the database’s schema and data.
First submit a recognisable job and wait for completion, then run:

```sh
docker compose exec -T db pg_dump -U dispatch -d dispatch > backup.sql
docker compose exec -T db createdb -U dispatch restored
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U dispatch -d restored < backup.sql
docker compose exec -T db psql -U dispatch -d restored -c 'SELECT id, title, status FROM jobs;'
```

`-T` disables the interactive terminal so redirection carries the SQL cleanly.
`>` saves output to the workspace file; `<` supplies that file as input.
`createdb` creates the separate restore target, and `psql` runs SQL against it.
`ON_ERROR_STOP=1` makes restoration stop if an SQL command fails.
The final query lists the restored jobs so you can find the one you submitted.

```figure
pg-dump-restore
```

Keep the application connected to `dispatch`; `restored` is only your recovery test.
If you repeat the exercise and `restored` already exists, inspect it before deciding to remove and recreate that practice database.
Never remove the live `dispatch` database to make the restore command work.
This guided backup is preparation for the capstone and is not part of this lesson’s automated pass.

Scale only the worker role here.
Adding workers is different from creating multiple database servers that share one writable directory; database replication needs its own design.
