# Use the signal that answers the question

Kubernetes events describe decisions and failures around objects, such as a scheduling rejection or failed image pull.
Container logs describe what a process chose to emit.
Metrics summarize behavior as time series.
These signals overlap, but none substitutes for all the others.
A healthy Pod can serve slow requests, and a failed metrics scrape can hide a healthy application.

Dispatch now logs a structured http_request event for each GET /jobs request, including request ID, status, elapsed time, and serving Pod.
It also exposes bounded-cardinality counters and a latency histogram at /metrics.
Only business reads enter that histogram; health checks and metrics scrapes do not inflate its denominator.
Counters reset when a process restarts, so interpret their rate over a window instead of subtracting arbitrary raw values across Pod replacements.

```sh
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl logs deployment/dispatch -c api --tail=30
kubectl get pods -l app=dispatch -o wide
kubectl get deployment prometheus
```

Prometheus discovers individual API Pods using the Kubernetes API and their named http container port.
Scraping a load-balanced Service would alternate between processes and mix their independent counters under one target identity.
Per-Pod discovery preserves that identity and attaches a pod label to each series.
The Prometheus service account can read Pods in this namespace; it does not need to read Secrets or administer the cluster.

A gauge can rise or fall, a counter accumulates events, and a histogram counts observations into cumulative upper-bound buckets.
For example, rate(example_requests_total[2m]) estimates requests per second over two minutes while accounting for counter resets.
The up metric records scrape success; up=1 says the target could be scraped, not that its users are happy.

The supplied monitoring.sh builds ConfigMaps from the authored files and restarts Prometheus so the new scrape configuration is actually loaded.
This exercise uses five-second scrape intervals to make the feedback loop visible locally.
Production retention, cardinality, resource sizing, access control, and alert routing need a separate operational design.
