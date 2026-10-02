## Taking a node out for maintenance

Before you patch, reboot, or replace a node, you move its workloads elsewhere.
Four separate things happen, and it helps to keep them apart when something gets stuck:

- **Cordon**: mark the node unschedulable, so no new Pods land on it. Running Pods stay.
- **Drain**: cordon it, then **evict** its Pods, asking each one to leave through the API.
- **Replace**: each evicted Pod’s controller, such as its Deployment, creates a new Pod.
- **Schedule**: the scheduler must find another node with room that the new Pod is allowed on.

A **PodDisruptionBudget (PDB)** can refuse an eviction if it would leave too few Pods running.
It protects availability, but it cannot create spare capacity or move storage that belongs to one node.

```figure
cordon-drain
```

```sh
kubectl cordon NODE
kubectl drain NODE --ignore-daemonsets --delete-emptydir-data --timeout=180s
kubectl uncordon NODE
```

- `--ignore-daemonsets` is almost always needed: DaemonSet Pods, such as Calico, belong on every node and would come straight back.
- `--delete-emptydir-data` allows evicting Pods with `emptyDir` volumes, whose contents are lost. Check that data really is disposable first.
- `--timeout` stops the command waiting forever.

## This lab

There is one control plane and two workers.
Dispatch’s two API copies run on different workers, and PostgreSQL with its local volume stays on the worker named in `$DOCKYARD_WORKER`.
The node to maintain is the other worker, `lima-$DOCKYARD_NODE_PREFIX-worker2`.

The PDB `dispatch-maintenance` currently requires both API copies to stay available, so it allows no eviction at all, and a drain would wait forever.

## Worked example: look before you evict

```sh
kubectl get nodes
kubectl get pods -o wide
kubectl get pdb dispatch-maintenance
kubectl get pods -A --field-selector="spec.nodeName=lima-$DOCKYARD_NODE_PREFIX-worker2"
```

`--field-selector spec.nodeName=...` lists only the Pods on that node.
For each, work out which controller owns it and whether it has storage tied to the node.
The API’s `/tmp` is a throwaway `emptyDir`, so evicting it is fine here, but do not assume that about every `emptyDir`.

## Change the budget, then drain

With two ready API copies, requiring one to stay available permits one eviction at a time.
Set `spec.minAvailable` to `1`, with `kubectl edit pdb dispatch-maintenance` or a patch, and check the PDB’s `ALLOWED DISRUPTIONS` becomes 1.
Then drain with the command above.

Never add `--disable-eviction`: it deletes Pods directly and ignores the budget.
If a drain stalls, check the PDB’s allowed disruptions, how many replicas are ready, events, placement rules, and whether another node has room.
The API uses *preferred* anti-affinity, so both copies may share the remaining worker during maintenance; *required* anti-affinity would make that impossible with only one worker left.

## What “done” looks like

Leave the drained worker cordoned so Check work can see it.
It should have no ordinary Pods left, two API copies should be available on other nodes, and new jobs should still complete.
Deleting the Node object or rebuilding the cluster is not the same as draining it.
In real maintenance you would finish the work and then `kubectl uncordon` the node.
