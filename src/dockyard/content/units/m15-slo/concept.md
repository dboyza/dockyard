# An SLI measures behavior; an SLO sets the target

An indicator needs an eligible population, a good-event definition, and an observation window.
This lab counts GET /jobs reads that return valid successful responses within 250ms.
Its objective is at least 95 percent good reads in the bounded local rehearsal.
The allowed bad fraction is 1 - 0.95 = 0.05.
For 200 eligible reads, that budget would allow at most ten bad reads in that sample.

Availability and latency are separate possible indicators.
A request can return HTTP 200 yet miss its latency target.
Health probes can remain healthy during that regression because process health and dependency reachability do not measure the full user experience.
Avoid redefining the indicator to hide slow requests or counting only successful responses in its denominator.

The supplied measure-slo.py runs twenty real reads inside the Pod network and records elapsed time, status, payload validity, and request ID for each.
This separates application/network behavior from Mac-to-VM port-forward overhead.
It writes slo-before.json or slo-after.json and computes the good/total ratio using slo.json.

```sh
python measure-slo.py before
kubectl get configmap dispatch-settings -o yaml
kubectl logs deployment/dispatch -c api --tail=40
```

The supplied delay_ms configuration intentionally affects business reads while readiness remains useful for dependency checks.
The delay is read from a mounted ConfigMap file on each request.
Projected ConfigMap updates are eventually delivered, so the reference restarts the API and waits for rollout to establish a definite new configuration before measuring again.
A production service might support an explicit reload mechanism instead.

Twenty local reads are a reproducible exercise, not a statistically reliable monthly production SLO.
Report the sample size, time window, observation location, excluded traffic, and threshold with the result.
A burn-rate alert compares observed bad-event rate with the allowed budget over chosen windows; sustained and short-window signals serve different operational purposes.
