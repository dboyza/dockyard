## Repair the maintenance schedule and prove it works

1. Look at the `dispatch-maintenance` CronJob and work out what is wrong with it.
2. In `maintenance.yaml`, make it run `python maintenance.py` every five minutes, not suspended, with `Forbid` concurrency and a small `backoffLimit`.
3. Apply the file.
4. Create a Job called `maintenance-proof` from the CronJob and wait for it to complete. Delete any earlier failed `maintenance-proof` first.
5. Read its logs and the `maintenance_runs` row in PostgreSQL.
6. Choose **Check work**.

The workers must keep processing new jobs while you do this.
