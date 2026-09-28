## Protect the database and prove recovery

1. Fix both claim retention settings on the StatefulSet in `platform.yaml`, and the dump command in `backup.sh`.
2. Apply the manifest, run `python storage-proof.py`, then run the fixed `backup.sh`.
3. Check the original marker from the replacement source Pod, and the two recovery records in `db-restore-0`.
4. Compare the claims and PVs of the source and restore databases to show they are separate.
5. Make sure the application still works after the proof interrupted the database.

Write a runbook listing the source and destination, the records to expect, the commands that verify them, and what this local setup would not survive.
