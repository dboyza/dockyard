# Repair the incomplete backup

The prepared source contains two recovery records, but `backup.sh` uses a schema-only dump.
The recovery target has tables without the required data.
Inspect both databases and the dump before editing.

Repair the dump command, run `python storage-proof.py` to demonstrate source durability, and rerun `sh backup.sh`.
The script resets only the dedicated db-restore database before restoring.
Verify both known records and the original marker in the target, then confirm source and target use different claims and PVs.
Do not copy files into a shared volume or query the source while calling it a restore.
