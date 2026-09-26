## Delivery and recovery contract

Diagnose why the prepared stack's original job is not completing, then repair the worker's dependency configuration.
Publish the supplied application to the assigned loopback registry and run both API and workers from its immutable digest.
Use at least two workers, healthy dependency gates, private database/queue endpoints, and the assigned owned PostgreSQL volume.

Keep API and every worker non-root, read-only, with all capabilities dropped and no-new-privileges enabled.
For each application role, use 32-256 MiB memory, a positive CPU quota at most one CPU, and a 16-256 process limit.
Do not apply an unsuitable read-only recipe blindly to PostgreSQL's writable data path.

Create a logical PostgreSQL backup and restore it into a separate database named `restored`.
Prove the original `capstone-$DOCKYARD_LAB` job exists there.
Leave the ordinary application database serving new jobs successfully.
Write RUNBOOK.md with the operational steps and your diagnosis.
The resulting source checkpoint is available after a passing check; its exclusion manifest explains omitted runtime or credential files.
