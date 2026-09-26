# Permission and preference are separate constraints

A node label is a fact used by selectors and affinity rules.
Required node affinity excludes nodes that do not match; preferred affinity expresses a scoring preference.
A NoSchedule taint repels new Pods unless they tolerate it.
A matching toleration permits a Pod onto the node but does not attract it there.
Dedicated placement commonly combines a node label/affinity with a matching taint/toleration.

This exercise has a control-plane node and two application workers.
The workers are labeled dockyard.pool=apps and tainted dockyard.pool=apps:NoSchedule.
The API must select that pool and tolerate its taint.
The database and small dependencies stay on the control-plane node for this constrained local rehearsal so draining an application worker does not strand node-local database storage.
That placement is an explicit local teaching compromise, not a production recommendation to host databases on control-plane nodes.

A topology spread constraint limits uneven replica distribution across a topology key.
Here kubernetes.io/hostname separates the two worker nodes, maxSkew 1 bounds the difference, and DoNotSchedule makes the bound a scheduling constraint.
Spread constraints do not create new capacity or override affinity and taints.

```sh
kubectl get nodes --show-labels
kubectl describe node "$DOCKYARD_CLUSTER-worker"
kubectl describe pods -l app=dispatch,track=stable
kubectl get pods -l app=dispatch,track=stable -o wide
```

Compare the nodes remaining after each constraint rather than changing several unrelated fields blindly.
The real nodes are containers in one Docker VM, so spreading across them exercises scheduling mechanics without creating independent physical failure domains.

The supplied matchLabelKeys includes pod-template-hash so a new Deployment revision spreads its own Pods independently of the retiring revision.
Scheduling constraints act when a Pod is placed; they do not continually rebalance existing Pods after a deletion or label change.
Inspect the final distribution after a rollout instead of assuming that a valid constraint implies perpetual balance.
