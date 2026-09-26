# Recover the service and its observation path

Capture a before window using measure-slo.py before repairing the slow configuration.
Restore per-Pod scraping, the dashboard latency query, and the sustained latency alert.
Restore the fast 20ms business-read configuration and wait for the actual API rollout.
Run the controlled alert rehearsal, which must fire under induced latency and clear after recovery.
Capture the final after window and keep the original 95 percent / 250ms policy.

Inspect the actual dashboard, target identities, request logs, alert evidence, and both SLO records.
Write a short incident note distinguishing the application regression from the monitoring faults, identifying the observation limits, and naming a prevention step for each.
Preserve the data claim and the normal background workers.
