## Find the original job in the restored service

Archive the closed database from `$DOCKYARD_VOLUME-source` into `backup.tar` in your workspace.
Its archive member must be named `jobs.db`.
Restore it into the separate target volume `$DOCKYARD_VOLUME` while the target API is stopped.
Give user 10001 access to the target, then restart the API.

Find the original `recovery-$DOCKYARD_LAB` job through `/jobs`, and submit a new job to test writes.
Preserve the source volume and leave the archive and restored API available for checking.
The checker inspects both the archive and the restored database, so an empty file named `backup.tar` is not enough.
