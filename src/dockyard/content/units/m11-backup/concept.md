## A backup only counts once you have restored it

Persistent storage protects data when a Pod is replaced.
It does not protect against deleting the wrong rows, a bad migration, or losing the whole cluster.
For that you need **backups**, and the only way to know a backup works is to restore it somewhere and look at the data.

## Logical backups with pg_dump

`pg_dump` writes a PostgreSQL database out as SQL statements that recreate its tables and rows.
This is a **logical** backup: it describes the data, not the files on disk, so it can be restored into any compatible PostgreSQL server.

In Kubernetes you run it inside the database Pod and save the output on your computer:

```sh
kubectl exec db-0 -- pg_dump -U dispatch -d dispatch --no-owner --no-acl > backups/dispatch.sql
```

`--no-owner` and `--no-acl` leave out ownership and permission details, which makes the file easier to restore into a different server.

Be careful with options that leave things out.
`--schema-only` writes the table definitions but **no rows**: restore it and you get empty tables.
A large file and a zero exit code do not prove the rows are in it.

## Restore somewhere separate

Never test a backup by restoring over the original: if the backup is bad, you have just destroyed the only good copy.

```figure
independent-restore
```
This lab has a second database, the `db-restore` StatefulSet, with its own claim and volume.
Restoring into it looks like this:

```sh
kubectl exec -i db-restore-0 -- psql -U dispatch -d dispatch -v ON_ERROR_STOP=1 < backups/dispatch.sql
```

`-i` passes your terminal’s input, here the backup file, into the container.
`ON_ERROR_STOP=1` makes psql stop at the first error instead of carrying on with a half-restored database.

The supplied `backup.sh` does all of this: dumps the source, starts `db-restore`, empties its data, and restores into it.
Read every line of it before running it, and never point it at `db-0`.

## Check the right things

```sh
kubectl exec db-0 -- psql -U dispatch -d dispatch -c 'SELECT * FROM recovery_records;'
kubectl exec db-restore-0 -- psql -U dispatch -d dispatch -c 'SELECT * FROM recovery_records;'
kubectl get pvc,pv
```

The restored database should show the same records as the source.
The two databases should use different claims and PVs, which proves the restore really is independent.

## What this backup does not cover

- It does not back up Kubernetes objects such as Deployments and Services; that is etcd’s job, covered in the cluster administration modules.
- The backup file sits on your computer. A real plan stores backups somewhere separate, protects them, keeps several, and rehearses restores regularly.
- How much data you could lose, and how long a restore takes, should match what the service needs. Measure both when you rehearse.
