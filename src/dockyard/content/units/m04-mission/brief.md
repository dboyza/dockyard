## Migration contract

Preserve the original job `recovery-$DOCKYARD_LAB` from the current API container.
Create `backup.tar` containing its quiescent jobs.db at the archive root.
Create a labeled named volume `$DOCKYARD_VOLUME`, restore the original data there, and replace the API container using that volume at `/data`.
Keep the non-root application image, lab label, assigned name, and loopback port.

The final service must return the original job and accept new writes.
Leave the usable archive in the workspace.
Explain the point at which removing the old container became safe and how you verified the replacement used the new storage resource.
