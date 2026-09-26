# Restore per-Pod scrape discovery

Prometheus is running, but prometheus.yaml keeps only a nonexistent named container port.
Inspect the API Pod port name and the discovery relabel rules.
Repair the keep rule to match the actual http port while retaining the app=dispatch selection and per-Pod identity label.
Run `sh monitoring.sh` and wait for both API targets to be healthy.
Inspect live up and request-counter series through Prometheus or the supplied dashboard.
Connect one real request to its structured log event and compare that process evidence with Kubernetes events.
Do not replace actual scraping with a recording rule that returns a constant up value.
