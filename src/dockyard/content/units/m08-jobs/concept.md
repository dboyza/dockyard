# Completion is a different success condition

A long-running service should remain available; a maintenance process should finish its task and exit.
A Job tracks completions and failed attempts, creating replacement Pods according to its retry policy.
`restartPolicy: Never` gives each failed attempt a separate Pod; `OnFailure` can restart the container within its Pod.
A bounded `backoffLimit` prevents endless retries from hiding a persistent failure.
Job Pod templates are generally immutable after creation, so a changed task normally needs a new Job.

A CronJob creates Jobs from a template according to its schedule.
`concurrencyPolicy: Forbid` prevents overlapping Jobs from that CronJob, while `Allow` permits them and `Replace` replaces the prior running Job.
Setting `suspend: true` pauses future scheduled creations without stopping Jobs already created.
Schedulers are not an exactly-once business transaction mechanism, so maintenance should tolerate retries.

## Worked example

```sh
kubectl get cronjob dispatch-maintenance
kubectl create job maintenance-proof --from=cronjob/dispatch-maintenance
kubectl wait --for=condition=Complete job/maintenance-proof --timeout=90s
kubectl logs job/maintenance-proof
```

The supplied `maintenance.py` records a real count of current jobs in PostgreSQL's `maintenance_runs` table.
Its row is keyed by Job name, so retrying one Job updates that observation instead of duplicating it.
The checker independently reads the table; printing a success-looking line is insufficient.
A manual Job proves the template can run now, while the CronJob fields establish the future scheduling contract.
It does not claim that the checker waited through every scheduled run.
