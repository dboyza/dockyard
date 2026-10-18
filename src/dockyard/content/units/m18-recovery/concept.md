## Restoring an encrypted backup onto new storage

The storage module restored a plain backup.
Real backups are usually encrypted, and restoring one safely involves a few more decisions.

## What happened before this lesson

`backup.py` has already:

1. submitted a unique job and waited for a worker to finish it, so there is a known record to look for;
2. made a consistent backup with `pg_dump`;
3. encrypted it with **AES-256-GCM**, using a random key stored in private lab data outside your workspace;
4. checked that a tampered copy fails to decrypt;
5. stopped the original database, keeping its storage, to simulate losing it.

GCM encryption also *authenticates* the data: if anyone changes a byte, decryption fails instead of producing corrupted data.

Encryption creates a new responsibility: **the key**.
Lose the key and the backup is useless; store the key right next to the backup and anyone who steals one has both.
Real systems keep keys in a separate, protected, recoverable key-management service.

```figure
encrypted-restore
```

## Restoring

`restore.py`:

1. decrypts the backup in memory;
2. creates a **new** database, `db-recovery`, with its own separate claim;
3. loads the backup into it and checks the known record is there;
4. only then changes the `db` Service’s selector so traffic goes to the new database.

The original database’s claim is left untouched, so if the restore turns out to be wrong you can switch back.

```sh
python restore.py
kubectl get statefulsets,pvc
kubectl get service db -o yaml
```

Both databases carry the label `app: db`, so the existing network rules already allow the API and workers to reach either.
The Service additionally selects `recovery: restored` to choose only the new one.

For a plain, unencrypted database, the equivalent commands would be:

```sh
pg_dump --clean --if-exists --no-owner --no-acl audit > audit.sql
psql -v ON_ERROR_STOP=1 restored_audit < audit.sql
```

## Recording what you did

A recovery runbook should name the symptom and who may authorize the restore.
It should say where the backup and its key are, and where you restored to.
It should also say how you checked the restore, how traffic was switched, and when you would switch back.
Measure how much data could be lost and how long recovery took, rather than assuming.
