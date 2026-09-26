# Match the controller to the work

A Pod is an execution unit, but a standalone Pod has no workload controller to replace it after deletion.
A Deployment maintains interchangeable replicas and supports rolling replacement.
Dispatch's API and queue workers use Deployments because either replica can serve the same role.
A worker stores job ownership and results in PostgreSQL, so replicas coordinate through durable rows rather than local process memory.

A DaemonSet maintains a Pod on each eligible node, which is useful for node-level agents.
Its desired count follows eligible nodes, not a user-selected replica count.
A Job manages finite work that must reach completion, while a CronJob creates Jobs on a schedule.
A StatefulSet supplies stable identities and ordered behavior for workloads that need them; a later module introduces its storage contract.

## Worked example

```sh
kubectl get deployment worker -o wide
kubectl describe deployment worker
kubectl get daemonset dispatch-node-agent
kubectl get pods -l app=dispatch-node-agent -o wide
kubectl logs deployment/worker --tail=20
```

Compare desired, current, and ready DaemonSet counts.
This one-node lab should have one ready agent; requesting two Deployment replicas would not mean one agent per node on a larger cluster.

The supplied database uses `emptyDir` here to keep the exercise focused on workload lifecycle.
It survives a database container restart inside the same Pod but is lost when that Pod is removed.
Do not treat this checkpoint as durable storage; the storage module replaces that deliberate limitation.
