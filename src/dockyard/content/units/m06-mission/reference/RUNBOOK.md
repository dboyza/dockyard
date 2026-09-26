# Dispatch operational handoff

## Start and inspect

Set DISPATCH_RELEASE to the digest published to the assigned local registry, then run `docker compose up -d --scale worker=2 --wait --wait-timeout 90`.
Inspect `docker compose ps`, request `/readyz`, and submit a new job through the API dashboard.
A successful job must show a computed result and the identity of a running worker in PostgreSQL.

## Configuration repair

The original worker pointed DB_HOST at a nonexistent service.
Restore the internal `db` service address and keep database and queue ports unpublished.
Keep application roles non-root with a read-only root filesystem, dropped capabilities, no-new-privileges, and measured resource limits.

## Backup and restore

Create a logical custom-format backup with `pg_dump -U dispatch -d dispatch -Fc` inside the assigned database container.
Save it as dispatch.dump, create the separate restored database, and use `pg_restore --exit-on-error` to restore there.
Verify the original capstone job exists in the restored database before considering recovery demonstrated.
A backup file by itself is not proof of a usable restore.

## Stop and resume

Use `docker compose stop` and `docker compose start`, or Dockyard's Stop and Resume controls for this lab.
Preserve the PostgreSQL and registry volumes when stopping.
Removing the project with its volumes discards this practice data and should be a deliberate reset.

## Transfer notes

The registry is local and unauthenticated for this practice environment.
Production release distribution needs appropriate authenticated transport, access control, provenance, and operational policies.
The local resource limits demonstrate enforcement and require measurement before adopting them for a real workload.
