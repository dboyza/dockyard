# Three questions deserve three signals

Startup asks whether initialization has completed.
While a startup probe has not succeeded, Kubernetes postpones the container's readiness and liveness probes.
This gives slow initialization an explicit bounded budget instead of forcing a large permanent liveness delay.
Dispatch deliberately warms up for twelve seconds and exposes `/startupz` for this local initialization state.

Liveness asks whether restarting this process is an appropriate recovery action.
Dispatch's `/healthz` checks that its HTTP process can respond without depending on PostgreSQL or Redis.
Using dependency-aware readiness as liveness can restart every API Pod during a database outage while doing nothing to repair the database.
Readiness asks whether the process should receive application traffic now.
Dispatch's `/readyz` checks warmup and both dependencies, so an unready Pod is removed from ready Service endpoints without necessarily being restarted.

## Worked example

```sh
kubectl describe pod -l app=dispatch,track=stable
kubectl get pods -l app=dispatch,track=stable -w
kubectl logs deployment/dispatch -c api --previous
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
```

A failed startup or liveness probe can restart a container after its failure threshold.
A failed readiness probe affects traffic eligibility.
Set budgets from observed startup and recovery behavior, rather than copying a short timeout everywhere.

During Pod termination, the grace period includes shutdown work such as a preStop hook if one is configured.
The process must handle SIGTERM and finish before forced termination becomes necessary.
The supplied `termination-proof.py` starts a separate disposable application Pod, sends SIGTERM to its process, and checks the exit.
It avoids interrupting the two application replicas merely to demonstrate process handling.
The lab does not claim that this small server drains arbitrary long-running production workloads.
