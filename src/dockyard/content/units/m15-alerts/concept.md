# A dashboard is a question expressed as a query

The supplied dashboard reads the real Prometheus HTTP API and graphs a three-minute window.
Its panels ask how many business reads arrive, what fraction exceed 250ms, and what the histogram estimates for p95 latency.
Open the loopback address printed by `printf 'http://127.0.0.1:%s\n' "$DOCKYARD_PORT"` in the browser.
The dashboard is a supplied learning component; its queries live in dashboard.json for inspection and repair.

A missing series means no observation, not a healthy zero.
An average can hide a slow tail, while a histogram quantile is an estimate whose precision depends on bucket boundaries.
When a decision uses an exact boundary, the corresponding bucket fraction is often clearer than a quantile estimate.
For example, a fraction of requests within a 500ms target can be written as:

```promql
sum(rate(example_request_duration_seconds_bucket{le="0.5"}[5m]))
/
sum(rate(example_request_duration_seconds_count[5m]))
```

The Dispatch alert instead measures the fraction slower than 250ms over one minute.
It becomes pending when that fraction exceeds 10 percent and firing after the condition lasts fifteen seconds.
The for duration prevents a single evaluation spike from immediately firing; it also delays detection.
Annotations describe user impact and the first investigation steps.
No external notification is sent in this local lab.

A rule that never fires is not validated by an empty alerts page.
The supplied alert-proof.py introduces a bounded 600ms delay, waits for a real firing alert and measured latency, then restores 20ms and waits for recovery.
The recovery runs in a finally block so an unsuccessful rehearsal still attempts to restore the fast configuration.
The script records both observed states and the exact rule/dashboard file hashes.
Inspect the rule, its pending/firing state, and the measured ratio together.
