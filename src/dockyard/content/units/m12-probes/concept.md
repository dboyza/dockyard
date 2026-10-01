## Three health questions, three probes

Kubernetes can check on a container regularly and act on the answer.
Each check is called a **probe**, and there are three kinds, each asking a different question:

| Probe | Question | If it fails |
| --- | --- | --- |
| **startup** | Has the app finished starting? | Keep waiting, up to a limit; then restart the container. The other probes do not run until this one succeeds. |
| **liveness** | Is the process stuck beyond saving? | Restart the container. |
| **readiness** | Should this Pod get traffic right now? | Remove the Pod from its Services’ endpoints until it passes again. Nothing is restarted. |

Choosing the right check for each is what matters.
Dispatch offers three addresses built for this:

- `/startupz` succeeds once Dispatch has finished warming up. In this lab that takes twelve seconds.
- `/healthz` succeeds whenever the process can answer at all, without checking the database or queue.
- `/readyz` succeeds only when Dispatch has warmed up *and* can reach PostgreSQL and Redis.

The classic mistake is using a dependency check such as `/readyz` for liveness.
If the database goes down, every API Pod fails liveness and restarts over and over, and none of that fixes the database.
Readiness is the right place for dependency checks: the Pods stop receiving traffic, then come back by themselves when the database recovers.

```figure
probe-roles
```

## Probe settings

```yaml
startupProbe:
  httpGet:
    path: /startupz
    port: 8080
  periodSeconds: 2
  failureThreshold: 15
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  periodSeconds: 5
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  periodSeconds: 2
```

- `periodSeconds` is how often the probe runs.
- `failureThreshold` is how many failures in a row count as failed.
- `timeoutSeconds` is how long one attempt may take (default one second).
- `initialDelaySeconds` waits before the first attempt. With a startup probe you rarely need it.

A startup probe’s **budget** is `periodSeconds × failureThreshold`: here 2 × 15 = 30 seconds to finish starting.
Set it from how long the app really takes, with some margin.

The starter already has a `livenessProbe` and a `readinessProbe`: change those in place rather than adding new ones.
If a key appears twice in the same YAML mapping, most tools silently keep only the last one, so an extra `livenessProbe` further down would quietly win.

Besides `httpGet`, a probe can use `exec` to run a command in the container (success means exit code 0), or `tcpSocket` to check a port accepts connections.

## Watch it happen

```sh
kubectl get pods -l app=dispatch,track=stable -w
kubectl describe pod -l app=dispatch,track=stable
kubectl logs deployment/dispatch -c api --previous
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
```

In this starter, liveness uses `/readyz`, which fails during warmup, so containers restart before they finish starting: the RESTARTS column keeps climbing.
`describe pod` shows events such as “Liveness probe failed”.
`logs --previous` shows the output of the container before its last restart.

## Stopping gracefully

When a Pod is deleted, Kubernetes sends its containers SIGTERM, waits up to `terminationGracePeriodSeconds` (default 30), then kills whatever is still running.
A `preStop` hook, if configured, runs first and counts against that time.
Dispatch handles SIGTERM and exits cleanly.

The workspace’s `termination-proof.py` starts a separate throwaway Dispatch Pod, stops it, and checks it exited cleanly, so your two real API Pods are not interrupted.
