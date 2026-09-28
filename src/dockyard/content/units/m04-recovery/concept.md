## Restore a backup into separate storage

A backup is useful only if you can recover the intended data from it.
This lab gives you two named volumes: a source containing a known job and an empty target used by the API.
You will copy the source into an archive, restore into the target, and find the original job through the API.

The source database has already been committed and closed, with no process writing to it.
That matters: copying a database file while it changes can produce an inconsistent backup.
For this small SQLite database, stopping writes before copying is sufficient.
Later, PostgreSQL uses its own backup tool instead of copying its live files.

## Create and inspect the archive

```sh
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -v "$DOCKYARD_VOLUME-source:/data:ro" \
  -v "$DOCKYARD_WORKSPACE:/backup" "$DOCKYARD_PYTHON_IMAGE" \
  tar -cf /backup/backup.tar -C /data jobs.db
tar -tf backup.tar
```

`tar` bundles files into an archive.
Here `-c` creates it, `-f` names it, and `-C /data` changes the directory before adding `jobs.db`.
The result contains `jobs.db` at its root, rather than a full filesystem path.
`-t` lists the contents without extracting them.
The source mount is read-only; the output is written into your workspace through the second mount.

## Restore and test the target

Stop the target API so it cannot write while you replace its database.
Extract into the assigned target volume and set the restored file’s owner:

```sh
docker stop "$DOCKYARD_CONTAINER"
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -v "$DOCKYARD_VOLUME:/data" \
  -v "$DOCKYARD_WORKSPACE:/backup:ro" "$DOCKYARD_PYTHON_IMAGE" \
  sh -c 'tar -xf /backup/backup.tar -C /data && chown 10001:10001 /data /data/jobs.db'
docker start "$DOCKYARD_CONTAINER"
```

`-x` extracts the archive.
The command changes ownership of only the target directory and restored database.
Once the API has started, request `/jobs` and look for `recovery-$DOCKYARD_LAB`.
Submit another job to check that the restored database is writable too.
Keep the source volume intact so a failed restoration does not destroy the original.

## If the data is inside a container

The next mission starts with the database in a container’s writable layer instead of a separate source volume.
After stopping that API, you can copy the closed file out before removing the container:

```sh
docker cp "$DOCKYARD_CONTAINER:/data/jobs.db" ./jobs.db
```

`docker cp` works with stopped containers.
It copies the file, not the whole application; you still need to archive it and restore it into the new volume.
Keep the original container until you have inspected your backup.

## Measure what you recovered

The **recovery point** is the time represented by the recovered data.
Changes made after that point will be missing.
The **recovery time** is how long it takes to make useful service available again.
For this exercise, identify both from your actual steps rather than from the archive’s filename.
