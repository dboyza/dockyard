## Fix, ship, secure, and recover Dispatch

- Find and fix why the workers cannot finish jobs.
- Push the application image to this lab’s registry and run both `api` and `worker` from its digest.
- Run at least two workers. Keep the health-check waits, the private database and queue, and the assigned PostgreSQL volume.
- Give `api` and every worker a read-only filesystem, no capabilities, no-new-privileges, 32-256 MiB of memory, at most one CPU, and 16-256 processes. Keep them non-root.
- Back up the `dispatch` database, restore it into a separate database named `restored`, and confirm `capstone-$DOCKYARD_LAB` is there.
- Leave the live application saving and finishing new jobs.
- Write `RUNBOOK.md` in the workspace.
