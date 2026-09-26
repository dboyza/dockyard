# Restore data into independent storage

A backup is useful only when its contents can be restored and checked.
A successful file copy or snapshot command says little about consistency, key custody, storage isolation, or application behavior after recovery.
This rehearsal uses a logical PostgreSQL dump and proves a previously completed job survives on a different persistent volume.

Before the fault, backup.py submits a unique job, waits for its real worker result, and creates a consistent pg_dump.
It encrypts the dump with AES-256-GCM using a random nonce and a private key outside the workspace.
Authenticated additional data binds the ciphertext to this lab and backup schema.
Changing ciphertext or its authentication tag must fail decryption.
The helper performs that negative test as part of the rehearsal.

Encryption does not make a backup self-sufficient.
Losing the key loses the ability to restore; keeping the key beside exported ciphertext defeats many storage-separation goals.
This exercise keeps the key in private lab data and excludes it from ordinary workspace exports.
A production recovery design needs an independently protected, recoverable key-management process.

For an unrelated audit database, a logical restore could use:

```sh
pg_dump --clean --if-exists --no-owner --no-acl audit > audit.sql
psql -v ON_ERROR_STOP=1 restored_audit < audit.sql
```

Our helper keeps the plaintext in memory and passes it directly to psql after authentication.
The original StatefulSet is scaled to zero, and its claim remains intact.
Restoration creates db-recovery with a separate claim, verifies the marker in that database, and then changes the db Service selector.
It does not overwrite the original claim or pretend that restarting the original Pod is a restore.

```sh
python restore.py
kubectl get statefulsets,pvc
kubectl get service db -o yaml
```

Both original and recovered database Pods carry app: db, so the previously taught API/worker network rules cover that role.
The Service adds recovery: restored to choose only the new instance.
The independently created StatefulSet and claim names keep their controller and storage identities distinct.

Write a recovery runbook with the symptom, authority to act, backup and key location, restore target, validation, traffic switch, and rollback conditions.
Measure the amount of data that can be lost and the time to recover rather than promising recovery from an untested procedure.
The checker decrypts the actual ciphertext, rejects an altered tag, compares distinct volume backing paths, verifies the preserved source claim, and reads the marker through the frontend.
