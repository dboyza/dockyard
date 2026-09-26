# A second release needs an explicit traffic contract

A canary exposes a limited candidate alongside a stable release so you can observe behavior before wider promotion.
This lab runs two stable replicas and one candidate replica, each owned by a different Deployment with disjoint track selectors.
The primary Service intentionally selects app=dispatch across both tracks.
A separate preview Service selects only track=canary for direct candidate validation.
Controller selectors must remain disjoint even when a Service selector spans both groups.

Replica counts are a coarse exposure mechanism, not a promise that exactly one third of requests reaches the candidate.
Connection reuse, proxy behavior, topology, and request patterns can skew traffic.
Precise weighted routing requires a suitable routing layer and its own verification.
The assessment checks ready endpoint membership and each release's response rather than demanding a statistically exact percentage.

## Worked example

```sh
kubectl get deployments,pods -l app=dispatch
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
kubectl get endpointslices -l kubernetes.io/service-name=dispatch-preview
kubectl exec deployment/dispatch -c api -- python -c 'import urllib.request; print(urllib.request.urlopen("http://dispatch-preview:8080/healthz").read().decode())'
```

Blue-green keeps two complete environments and switches an entry point from one to the other after validation.
It favors a clear promotion boundary and quick traffic reversal, but requires enough duplicate capacity and careful treatment of shared state.
You can model its selector switch with these two tracks, but the required final lab state remains a canary plus a candidate-only preview.
For either pattern, define abort criteria from errors, latency, data correctness, and operational signals before promotion.
