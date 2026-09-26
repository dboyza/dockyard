# Repair and prove the maintenance schedule

The CronJob is suspended and its template runs an invalid script.
Configure `dispatch-maintenance` to run every five minutes with `Forbid` concurrency, bounded retries, and the supplied `maintenance.py` command.

Apply the repaired template, create `maintenance-proof` from that CronJob, and wait for completion.
If a failed proof Job already exists, delete that single practice Job before creating a replacement; editing the CronJob does not rewrite existing Jobs.
Inspect both logs and the actual maintenance row in PostgreSQL.
The worker fleet must continue processing fresh jobs while maintenance succeeds.
