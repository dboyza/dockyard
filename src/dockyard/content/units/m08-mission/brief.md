## Get every workload doing its job

Fix the supplied manifests so that:

- two API copies and two workers are running and a new job gets completed;
- the `dispatch-node-agent` DaemonSet runs on every node it should;
- `dispatch-maintenance` runs `python maintenance.py` every five minutes with `Forbid` concurrency and a small retry limit;
- a Job named `maintenance-proof`, created from that CronJob, completes and writes its row to `maintenance_runs`.

Then write `WORKLOADS.md` explaining why each controller fits its job, what could run twice if a retry happens, and when the database’s current data would be lost.
Check work tests the live cluster; your write-up is for your own review and your portfolio.
