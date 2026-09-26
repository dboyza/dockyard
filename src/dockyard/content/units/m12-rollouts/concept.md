# Desired state can describe a broken release

A Deployment can accept an image change that never becomes runnable.
The API accepting a manifest establishes only that it passed admission and validation.
Rollout status, Pod events, and application requests establish whether the release actually works.
This starter first ran the good release, then requested a nonexistent local image.
The failed revision remains visible in ReplicaSet history.

For two desired replicas, maxUnavailable 0 and maxSurge 1 permit a third temporary Pod while preserving the old available replicas until replacements become ready.
These settings require enough capacity for the surge and depend on meaningful readiness checks.
They cannot guarantee availability if an unrelated failure removes existing replicas or the application has incompatible state changes.

```sh
kubectl rollout status deployment/dispatch --timeout=20s
kubectl rollout history deployment/dispatch
kubectl get replicasets -l app=dispatch,track=stable
kubectl describe pods -l app=dispatch,track=stable
kubectl rollout undo deployment/dispatch
```

Undo restores an earlier Pod template, but it does not edit your local manifest.
If the file still names the broken image, the next apply can reintroduce it.
Repair the source of desired state as well as the running resource.
A rollback also does not reverse database migrations, external side effects, or unrelated configuration changes.
Use backward-compatible data changes and an explicit recovery plan.
