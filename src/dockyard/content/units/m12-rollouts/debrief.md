## Two places to fix

`rollout undo` restored the running Deployment; editing `platform.yaml` stopped the next apply from breaking it again.
Because the update could not remove old Pods until new ones were ready, users kept being served throughout.

Check your understanding:
With four replicas, `maxSurge: 1` and `maxUnavailable: 1`, what is the most Pods that can exist, and the fewest that must be available, during an update?
New Pods are Running but their readiness probe fails. Should you continue the rollout?
