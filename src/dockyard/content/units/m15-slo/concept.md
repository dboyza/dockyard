## Saying how reliable “reliable enough” is

Teams need a shared, measurable answer to “is the service good enough right now?”.
Three terms give it a precise shape:

- A **service level indicator (SLI)** is a measurement: the fraction of eligible events that were good.
- A **service level objective (SLO)** is the target for that measurement over a time window, such as “at least 95% good”.
- The **error budget** is what the target leaves over: with a 95% target, 5% of events may be bad.

Every SLI needs three decisions written down:

1. **Which events count?** Here: `GET /jobs` reads.
2. **What makes one good?** Here: a valid successful response within 250 ms.
3. **Over what window?** Here: one short measured sample.

With a 95% objective, 200 eligible reads may include at most ten bad ones.

## Honest measurement

It is easy to make an SLI look better than reality:

- Counting only successful responses in the total hides failures.
- Dropping slow requests from the total hides slowness.
- Using health checks as the measure hides everything users actually do.

A request can succeed with HTTP 200 and still be bad because it was slow.
Readiness probes can stay green through a slowdown, because they check that the process and its dependencies respond, not how quickly users are served.

## This lab

Dispatch has been configured to wait 600 ms before answering business reads, set by `delay_ms` in the `dispatch-settings` ConfigMap.
The supplied `measure-slo.py` makes twenty real reads from inside the cluster, records the time, status, and request ID of each, and calculates the good fraction using the objective in `slo.json`.
Measuring from inside the cluster avoids counting the extra time of the tunnel from your computer.

Make sure the API is ready first; otherwise the reads fail to connect and you measure an outage instead of the slowdown:

```sh
kubectl rollout status deployment/dispatch --timeout=120s
python measure-slo.py before
kubectl get configmap dispatch-settings -o yaml
kubectl logs deployment/dispatch -c api --tail=40
```

The delay is read from a mounted file, which updates on its own within a minute or two.
To measure from a definite point, apply the change, restart the API, and wait for the rollout before measuring again:

```sh
python render.py settings.yaml | kubectl apply -f -
kubectl rollout restart deployment/dispatch
kubectl rollout status deployment/dispatch --timeout=120s
python measure-slo.py after
```

## What twenty requests can and cannot show

Twenty reads are enough to see the calculation work and a clear before-and-after difference.
They are far too few to promise a monthly reliability level.
Whenever you report an SLO result, include the sample size, the time window, where it was measured, what was excluded, and the threshold.

Real teams also alert on the **burn rate**, how fast the error budget is being used up, over both a short and a long window, so a sudden outage and a slow leak are both noticed.
