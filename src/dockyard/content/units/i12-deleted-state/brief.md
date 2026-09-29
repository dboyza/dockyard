## Bring back the deleted objects

- Restore the trusted frontend Deployment and the `maintenance-sentinel` ConfigMap with their original UIDs, from the snapshot at `/var/lib/etcd/dockyard-recovery.db`.
- Restore into a new directory and switch the etcd manifest to it; do not overwrite etcd's current data.
- Keep the original nodes, namespace, database claim, and stored job.
- Show the API is ready, a new Pod gets scheduled, and a new job from the restored frontend completes.

In your notes, record what else a restore like this would roll back, and why the database's data needed no restore.
