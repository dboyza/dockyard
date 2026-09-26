# A backup is a hypothesis until restored

A logical PostgreSQL dump records database objects and, unless excluded, their data.
A schema-only dump can recreate tables while losing every business row.
A successful command exit or a large file therefore does not establish recoverability.
Restore into an independent destination and query records that matter.

This exercise supplies two known recovery records and a unique lab marker before backup.
The db-restore StatefulSet uses its own generated claim and volume.
The restore script replaces only that dedicated recovery database's public schema, leaving the source database intact.
Do not redirect those commands at db-0.

```sh
kubectl exec db-0 -- pg_dump -U dispatch -d dispatch --no-owner --no-acl > backups/dispatch.sql
kubectl exec -i db-restore-0 -- psql -U dispatch -d dispatch -v ON_ERROR_STOP=1 < backups/dispatch.sql
```

`backup.sh` includes destination creation, readiness, and an explicit reset of the recovery schema so it can be rerun.
Review every command before executing it.
The example uses a plain SQL dump for inspectability; custom-format dumps and pg_restore provide additional selection and parallel restore options.

A logical dump is not an etcd snapshot and does not back up Kubernetes resources.
A filesystem copy of a running database also needs database-aware consistency guarantees.
The cluster recovery phase handles control-plane state separately.

The local backup remains on this Mac.
A production recovery plan needs independent storage, access controls, retention, and restore rehearsals, with recovery point and recovery time objectives that match the service's needs.
