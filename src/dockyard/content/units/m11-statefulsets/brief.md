## Bring the database back without risking its claims

The database StatefulSet is scaled to zero, and it is set to delete its claims when scaled down or deleted.

1. Look at its `replicas` and `persistentVolumeClaimRetentionPolicy`.
2. In `platform.yaml`, set one replica and `Retain` for both `whenDeleted` and `whenScaled`. Keep the claim template and the headless Service.
3. Run `sh run.sh` and wait for `statefulset/db` to roll out.
4. Note `db-0`’s UID, claim, and PV, run `python storage-proof.py`, and compare them afterwards.
5. Choose **Check work**.

Keep PostgreSQL at one replica.
In your notes, explain why the new `db-0` has the same name but a different UID.
