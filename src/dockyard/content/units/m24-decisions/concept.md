## Work from constraints instead of larger numbers

This environment has one application worker and small control-plane guests.
Two API replicas improve process-level rollout continuity, but both still depend on the same worker and database volume.
Do not describe that placement as protection against losing the worker.
A production capacity decision would also require measured demand, failure-domain placement, and database recovery targets.

For this exercise, run two to four API replicas with positive CPU and memory requests.
The API's aggregate requests must stay at or below one CPU and 512 MiB; aggregate memory limits must stay at or below 1 GiB.
Every container limit must be at least its corresponding request.
These are explicit lab operating constraints, not estimates of production demand.
The checkpoint's existing per-container requests and limits already fit two replicas.

## Worked example: calculate before scaling

```sh
kubectl get deployment dispatch -o yaml
kubectl describe node "lima-$DOCKYARD_WORKER"
kubectl get pdb
```

Use the actual Kubernetes node name from `kubectl get nodes`; in this native profile it has a `lima-` prefix.
For example, two replicas requesting 100m CPU and 64Mi each request 200m and 128Mi in total.
A 256Mi memory limit per replica permits 512Mi in aggregate.
Scheduling considers requests; the memory limit constrains a running container and can produce an OOM termination.
Neither number is a substitute for observing demand.

Create `dispatch-operations`, a PodDisruptionBudget selecting the stable Dispatch API Pods and protecting at least one available replica.
For this exercise use `minAvailable: 1`, `minAvailable: 50%`, or `maxUnavailable: 1` with two replicas.
A disruption budget constrains voluntary evictions; it does not prevent crashes or guarantee that a rollout, node failure, or database remains available.
Wait for the requested API replicas to converge and become available.

## Permissions are part of the operating budget

The inventory Deployment uses the `dispatch-reader` service account.
It needs to list Pods in `dispatch`, not read Secrets, modify Deployments, or create RoleBindings.
The fixture replaces its namespaced Role with wildcard access and scales the API down to one replica.
Restore the intended Role from `identity.yaml` or author equivalent least-privilege rules.
Keep the existing identity and RoleBinding so the real workload exercises the repair.

The assessment uses the inventory Pod's mounted token and verified cluster TLS to perform real API requests.
It expects allowed Pod reads and denied Secret and cross-namespace reads, then checks mutation permissions separately.
A plausible-looking Role is supporting evidence; observed authorization establishes the requested boundary.
Complete a fresh Dispatch transaction after tightening access.
