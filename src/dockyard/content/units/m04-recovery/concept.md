## A file named backup is not evidence of recovery

A usable backup must contain the intended state, remain readable, and restore into an environment that can serve that state.
This exercise keeps a known source volume and an independent target volume so you can establish those properties without overwriting the source.
The source contains an original job with a lab-specific identity.
The target begins empty.

## Quiesce or use an application-aware backup

Copying files while a database is writing can capture an inconsistent point in time.
A production database has backup mechanisms for consistency, including its transaction logs and recovery requirements.
For this small SQLite fixture, the source database was created, committed, and closed before the lab begins.
No writer is attached to that source volume, so its data is quiescent.
This lab does not claim that a generic tar of a running PostgreSQL data directory is a valid database backup.

## Worked example: archive a stopped source

```sh
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -v "$DOCKYARD_VOLUME-source:/data:ro" -v "$DOCKYARD_WORKSPACE:/backup" \
  "$DOCKYARD_PYTHON_IMAGE" tar -cf /backup/backup.tar -C /data jobs.db
```

The source mount is read-only, the output stays in this lab's workspace, and the archive contains the database file rather than an absolute host path.
Inspect an archive's member names before restoring it.
Treat archives from an untrusted source as untrusted input; do not extract them over arbitrary host directories.

## Restore into a separate target

The target is `$DOCKYARD_VOLUME`, distinct from the `-source` volume.
Restore jobs.db there and give the non-root API access to it.
Then request `/jobs` from the target API and find the original job.
The checker also reads the target with an independent read-only container and checks that backup.tar itself contains a usable database with that job.

## Recovery point and recovery time

The recovery point describes how much recent data may be missing relative to the incident.
Recovery time describes how long it takes to restore useful service.
Neither is established merely by a successful archive command.
In your notes, identify the recovery point of this deliberately quiescent fixture and which operations consumed restoration time.
