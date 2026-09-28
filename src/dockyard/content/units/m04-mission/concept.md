## Move existing jobs into a named volume

Dispatch is running, but its original job lives inside the container’s writable layer.
Removing that container now would lose the job.
Your task is to move the database into a named volume and prove that the replacement API can use it.

Use the backup and restore steps from the previous lesson.
Plan the order before you begin: stop writes, copy and inspect the database backup, restore into separate storage, then replace the API.
Keep the old container until the backup is usable.
A newly created empty database would make the API appear healthy while losing the user’s work.

The original job is named `recovery-$DOCKYARD_LAB`.
Use that identity to distinguish successful recovery from a fresh installation.
