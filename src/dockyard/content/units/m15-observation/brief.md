## Get Prometheus scraping both API Pods again

Prometheus is running, but `prometheus.yaml` keeps only a container port name that does not exist, so it scrapes nothing.

1. Find the API container’s port name, and compare it with the relabel rules.
2. Fix the port-name `keep` rule to match the real port. Keep the `app=dispatch` rule and the `pod` label.
3. Run `sh monitoring.sh` and wait for both API targets to be up.
4. Look at the `up` and request-counter series in Prometheus or the supplied dashboard.
5. Make a request, find its `http_request` log line, and compare it with what `kubectl get events` shows.
6. Choose **Check work**.

Do not replace real scraping with a rule that always reports `up`.
