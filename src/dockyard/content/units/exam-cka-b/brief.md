# Native cluster maintenance assessment

Eight tasks, each with its weight, on this lab's two-node kubeadm cluster.
Do task 3, the scheduler, first: draining and upgrading need a working scheduler.
Do task 7, the disruption budget, after the upgrade.
Use the existing nodes; do not reset, rejoin, or rebuild them.

## 1. Upgrade the cluster to 1.37.1 (25%)

Upgrade this kubeadm cluster from 1.36.5 to 1.37.1: kubeadm, the control plane, and the kubelet on both nodes.

- `python -m dockyard.native stage-upgrade` copies the 1.37.1 packages into each VM; it does not install them.
- Drain each node before upgrading its kubelet, and uncordon it afterwards.
- Keep the package holds on kubeadm, kubelet, and kubectl.
- Both original nodes must end up Ready and schedulable.

Finish task 3 before you start, and create task 7's disruption budget only after the upgrade.

## 2. Renew the API server certificate (10%)

Renew the API server's serving certificate on the control-plane node, signed by the existing cluster CA.
The running API server must actually serve the new certificate; a renewed file on disk is not enough.
Do not replace the CA or turn off certificate checking.

## 3. Bring back the scheduler (10%)

The scheduler's static Pod manifest was moved out of `/etc/kubernetes/manifests` to `/var/lib/dockyard/maintenance-exam/kube-scheduler.yaml` on the control-plane node.

- Put it back so the scheduler runs again.
- Keep the other control-plane components and the kubelet running.

A new Pod must be scheduled onto a node.
Do this before tasks 1 and 7.

## 4. Allow an automation account to scale Deployments (10%)

ServiceAccount `release-operator` exists in namespace `dispatch`.
In that namespace, give it:

- `get` and `list` on Deployments;
- `get`, `patch`, and `update` on the `deployments/scale` subresource.

It must not be able to read Secrets, create Pods, or delete, patch, or update Deployments themselves.
Check with `kubectl auth can-i`.

## 5. Fix the Service selector (10%)

Service `dispatch` has an extra selector, `release: retired`, that no Pod matches.

- Remove it, keeping the rest of the selector and port 8080.
- The Service must send traffic to exactly the two ready API Pods, and the frontend must get the API's real `/healthz` response through it.
- Do not use `publishNotReadyAddresses` or bypass the Service.

## 6. Fix a NetworkPolicy without opening it up (15%)

The API can no longer reach its Redis queue, Service `queue` on TCP port 6379, because of a NetworkPolicy change.

- Restore that connection.
- Keep everything else the policies allow and deny: the trusted frontend allowed, the untrusted frontend and other namespaces denied, other API egress denied, and database, worker, and DNS (TCP and UDP) traffic allowed.
- Do not remove the policies or replace them with an allow-all rule.

## 7. Protect the API during maintenance (10%)

Create PodDisruptionBudget `dispatch-maintenance` in namespace `dispatch` that selects both stable API Pods.
With two healthy replicas, it must allow exactly one voluntary disruption.
Keep both API replicas running and available at the end.
Create it after the task 1 upgrade: on this cluster both API Pods run on the one worker, so while it is drained they have nowhere else to go, and the budget would stop the drain from finishing.

## 8. Keep the application working (10%)

At the end, the original namespace, both Node objects, the `maintenance-sentinel` ConfigMap, and the stored job must still be there.
A new Dispatch job sent from the frontend must complete and be saved in PostgreSQL.
