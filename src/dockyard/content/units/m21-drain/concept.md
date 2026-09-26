## Four different questions during node maintenance

Cordoning prevents ordinary new scheduling onto a node.
Draining asks the API to evict its ordinary workloads and waits for those Pods to leave.
A Deployment creates replacements, while the scheduler must find another eligible node with capacity.
A PodDisruptionBudget constrains voluntary eviction but does not manufacture replicas, capacity, or storage mobility.
Keep these boundaries separate when a drain stalls.

This lab has one control plane and two workers.
Two Dispatch API replicas initially occupy different workers, while PostgreSQL and its local volume remain on the worker named by `DOCKYARD_WORKER`.
The extra worker, `$DOCKYARD_NODE_PREFIX-worker2`, is the maintenance target.
The current budget requires both API replicas to remain available, so it permits no voluntary disruption.

## Worked example: inspect before evicting

```sh
kubectl get nodes
kubectl get pods -o wide
kubectl get pdb dispatch-maintenance
kubectl get pods -A --field-selector="spec.nodeName=lima-$DOCKYARD_NODE_PREFIX-worker2"
```

Identify each Pod's controller and any storage tied to its node.
The Calico and service-proxy DaemonSets belong on every eligible node, so normal drain uses `--ignore-daemonsets`.
The API's `/tmp` volume is disposable scratch data; allowing removal of that emptyDir is acceptable for this fixture.
That permission is not a claim that every emptyDir in a real cluster is disposable.
The local database PV stays on the other worker throughout this exercise.

## Change the budget, then drain

With two ready API replicas, retaining one during maintenance permits one eviction.
Update the budget to express that requirement, inspect its status, and drain the extra worker with a bounded timeout.
For example, the budget change can use `kubectl edit pdb dispatch-maintenance` or a merge patch setting `spec.minAvailable` to `1`.
The node command is:

```sh
kubectl drain "lima-$DOCKYARD_NODE_PREFIX-worker2" --ignore-daemonsets --delete-emptydir-data --timeout=180s
```

Do not use `--disable-eviction` to bypass the budget.
If an eviction stalls, inspect `disruptionsAllowed`, ready replicas, events, placement constraints, and free capacity.
Preferred anti-affinity normally separates the API replicas but allows both to share the surviving worker during maintenance.
Required anti-affinity would make that replacement impossible with only one eligible worker left.

## Prove the resulting boundary

Leave the maintenance target cordoned for assessment.
It should have no ordinary active Pods, while two API replicas become available elsewhere and fresh Dispatch work still completes.
The checker also verifies the original node and namespace identities and a stored database row.
Deleting the Node object or rebuilding the cluster cannot substitute for evacuating it.
In a completed real maintenance window, inspect the repaired node and use `kubectl uncordon NODE` before returning it to service.
Here, reset or clean the owned lab after reviewing the result.
