## Prove a separate restore

The source volume `$DOCKYARD_VOLUME-source` contains the original job; it has no active writer.
The assigned API uses a separate empty target volume `$DOCKYARD_VOLUME`.

Create `backup.tar` in the workspace with jobs.db at the archive root.
Restore that database into the target volume and ensure the non-root API can read and write it.
Preserve the source volume.
Verify `/jobs` on the target contains the original `recovery-$DOCKYARD_LAB` record and that new jobs can also be committed.
Leave both the archive and the restored service available for checking.
