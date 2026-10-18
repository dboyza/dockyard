## Recover the service and the ability to see it

1. Run `python measure-slo.py before` before changing anything.
2. Fix per-Pod scraping in `prometheus.yaml`, the latency query in `dashboard.json`, and the alert in `rules.yaml`, then run `sh monitoring.sh`.
3. Set `delay_ms` back to `20`, apply it, restart the API, and wait for the rollout.
4. Run `python alert-proof.py`; it must see the alert fire under induced slowness and clear afterwards.
5. Run `python measure-slo.py after`, keeping the 95% / 250 ms objective.
6. Choose **Check work**.

Look at the dashboard, the Prometheus targets, the request logs, `alert-evidence.json`, and both SLO records.
Write a short incident note.
Separate the application slowdown from the monitoring faults.
State what your measurements can and cannot show, and name a prevention step for each fault.
Keep the database storage and the normal workers running.
