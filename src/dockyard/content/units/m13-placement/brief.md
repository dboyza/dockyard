## Put the API on its dedicated workers

The API’s required affinity names a pool that does not exist, and its toleration has the wrong value.

1. Look at the node labels, the workers’ taints, and the API Pods’ scheduling events.
2. Fix `platform.yaml` so the API requires `dockyard.pool=apps` and tolerates `dockyard.pool=apps:NoSchedule`.
3. Keep the topology spread constraint and two replicas.
4. Apply the rendered manifest, wait for the rollout, and confirm there is one API Pod on each worker.
5. Choose **Check work**.

Do not remove the workers’ taints, loosen the affinity to allow any node, or move the API onto the control plane.
In your notes, explain why adding only the toleration would not guarantee the API ends up on the workers.
