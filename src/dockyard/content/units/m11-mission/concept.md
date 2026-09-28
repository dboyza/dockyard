## Keep the data, and prove you can get it back

The database has persistent storage, but two things put its data at risk:
its StatefulSet is set to delete its claims, and the backup script does not actually back up the rows.

This mission brings together the three storage lessons.
There are no step-by-step commands, but here is the goal:

1. The source database keeps its claims even if the StatefulSet is scaled down or deleted.
2. The source data survives its Pod being replaced.
3. A backup restored into the separate `db-restore` database contains both known records.
4. You can explain what this setup would still lose.

The existing source data is exactly what you are trying to protect, so inspect before changing anything, and never run anything destructive against `db-0`.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
