## Fix the backup so it contains the data

The source database `db-0` holds two recovery records and a marker, but `backup.sh` makes a schema-only dump, so the restored database has empty tables.

1. Compare the `recovery_records` table in `db-0` and `db-restore-0`, and look at the `pg_dump` options in `backup.sh`.
2. Fix the dump command so it includes the data.
3. Run `python storage-proof.py` to show the source keeps its data across a Pod replacement.
4. Run `sh backup.sh` again, then check both records and the marker are in `db-restore-0`.
5. Confirm the two databases use different claims and PVs.
6. Choose **Check work**.

Do not copy files into a shared volume, and do not query the source and call it a restore.
