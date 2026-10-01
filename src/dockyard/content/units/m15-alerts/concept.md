## From numbers to decisions

A graph is only useful if it answers a question you care about.
An **alert** goes further: it watches a question continuously and tells someone when the answer is bad.
This lesson builds both for one question: “what fraction of Dispatch’s `/jobs` reads are slower than 250 ms?”

## Reading the dashboard

The supplied dashboard queries Prometheus and graphs the last three minutes.
Open it in your browser at the address printed by:

```sh
printf 'http://127.0.0.1:%s\n' "$DOCKYARD_PORT"
```

Its queries live in `dashboard.json`, which you can read and edit.
Two things to keep in mind when reading any dashboard:

- **No data is not the same as zero.** A missing line can mean nothing is being measured at all.
- **Averages hide slow requests.** A few very slow requests barely move the average, so look at the share of slow requests or at a high percentile.

## Measuring “slow” from a histogram

A latency histogram counts requests into buckets by upper limit.
The series ending in `_bucket` with `le="0.25"` counts requests that took 0.25 s or less, and the series ending in `_count` counts all of them.
So the fraction that were **fast enough** is:

```promql
sum(rate(dispatch_http_request_duration_seconds_bucket{le="0.25"}[1m]))
/
sum(rate(dispatch_http_request_duration_seconds_count[1m]))
```

The fraction that were **too slow** is one minus that; PromQL lets you write `1 - (...)` around any expression.

`rate(...[1m])` looks at the last minute, and `sum` adds the numbers from both API Pods together.
A **percentile** such as `histogram_quantile(0.95, ...)` estimates the time under which 95% of requests finished, but it is only as precise as the bucket boundaries.
When your target is an exact boundary like 250 ms, the bucket fraction above is clearer.

```figure
histogram-buckets
```

## Writing the alert

```yaml
- alert: DispatchLatencyBudgetBurn
  expr: YOUR_SLOW_FRACTION > 0.1
  for: 15s
  labels:
    severity: warning
  annotations:
    summary: More than 10% of Dispatch reads exceed 250ms
    runbook: What to check first.
```

- `expr` is the condition; the alert is active while it returns a value.
- `for: 15s` means the condition must hold for fifteen seconds before the alert **fires**. Until then it is **pending**. This avoids alerting on one brief spike, at the cost of noticing a little later.
- `annotations` tell whoever receives the alert what it means and where to start.

```figure
alert-states
```

This lab does not send notifications anywhere; you watch the alert’s state instead.

## Proving an alert works

An alert that has never fired has not been tested.
The supplied `alert-proof.py` makes Dispatch deliberately slow (600 ms per request), waits for your alert to really fire, then restores normal speed and waits for it to clear.
It restores the fast setting even if something goes wrong halfway, and saves what it saw in `alert-evidence.json`.
