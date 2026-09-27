## Availability can hide a stalled release

The API Deployment uses a rolling strategy with no unavailable replicas and one surge replica.
The fixture changes its desired image to an unavailable local image.
Existing replicas may keep serving requests while the new revision cannot start.
A successful health request therefore does not establish that the desired release finished.
Inspect desired, updated, available, and total replicas separately.

## Worked example: choose a bounded recovery

```sh
kubectl rollout status deployment/dispatch --timeout=20s
kubectl rollout history deployment/dispatch
kubectl get deployment dispatch -o wide
kubectl get pods -l app=dispatch -o wide
```

Inspect the new Pod's events to distinguish an unavailable image from an application startup error.
The previously running revision is known to work in this exercise.
Use `kubectl rollout undo deployment/dispatch`, or correct the desired image to a valid built and loaded artifact, and wait for the rollout to converge.
Verify that updated and available replicas match the desired count and that the extra failed rollout Pod has gone.
Then complete a new job rather than stopping at process health.

Rollback is not a universal data recovery mechanism.
It restores a Deployment revision; it does not reverse database migrations, recover deleted volume contents, or rotate compromised credentials.
Document those boundaries so the next operator does not overinterpret the command.

## A handoff should let someone act

Write `handoff.md` for an operator who did not watch your terminal.
Include the current private context and namespace, the failed revision's symptom, the evidence behind the repair, and the commands that inspect the resulting state.
For each verification command, explain the expected observation and what a failure means.
Describe rollback and escalation conditions, the location and scope of relevant backups, and the explicit limits of this single-worker environment.
Do not include kubeconfig contents, tokens, database passwords, or private keys.

A source checkpoint preserves this document alongside portable infrastructure files and observed assessment evidence.
Its provenance distinguishes supported practice from an independent attempt.
The handoff's reasoning is reviewed with a visible self-review rubric; automated checks verify runtime convergence and actual application behavior, not the truth of prose.
