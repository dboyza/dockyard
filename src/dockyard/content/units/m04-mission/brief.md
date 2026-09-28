## Preserve the job during the move

Create `backup.tar` in your workspace from the stopped API’s database, with `jobs.db` at the archive root.
Create the named volume `$DOCKYARD_VOLUME` with the lab ownership label, and restore the original data into it.

Replace the API using that volume at `/data`.
Keep the supplied non-root image, assigned container name, lab label, and local port.
The final service must return `recovery-$DOCKYARD_LAB` and accept new jobs.
Leave the usable archive in the workspace for the checker.

In your notes, identify when removing the old container became safe and how you confirmed the replacement used the new volume.
The checker verifies data recovery; review the reasoning yourself.
