## Maintenance without an outage

Nodes need maintenance: operating system updates, restarts, replacement.
To work on a node safely you **drain** it, which evicts its Pods so they are rescheduled elsewhere, while disruption budgets keep enough copies serving.
This mission brings the whole module together: placement, resources, autoscaling, and a disruption budget, then a real drain under load.

Right now:

- the API’s placement rules stop it using the worker pool;
- the HPA targets the wrong Deployment;
- the disruption budget, at four replicas, allows no Pod to be removed at all.

Fix those before any maintenance.
There are no step-by-step commands.

## The drain rehearsal

`drain-proof.py` picks one application worker, notes the current API Pods, and drains the worker using the eviction API, which respects disruption budgets.
While it drains, it checks readiness through the NodePort, then uncordons the worker and waits for everything to settle.
It writes what it saw to `drain-evidence.json`.
Those are samples taken during one rehearsal, not proof that no request anywhere failed.

The commands it relies on are ones you will use in cluster administration:

```sh
kubectl cordon NODE_NAME
kubectl drain NODE_NAME --ignore-daemonsets --delete-emptydir-data
kubectl uncordon NODE_NAME
```

`cordon` stops new Pods being scheduled on a node; `drain` cordons it and evicts its Pods; `uncordon` makes it schedulable again.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
