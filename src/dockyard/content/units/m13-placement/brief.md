# Make both dedicated workers eligible

The API's required affinity names a nonexistent pool and its toleration has the wrong value.
Inspect node labels, taints, and scheduling events.
Repair `platform.yaml` so the API requires dockyard.pool=apps and tolerates dockyard.pool=apps:NoSchedule.
Preserve the supplied topology spread constraint and two stable replicas.
Apply the rendered manifest, wait for rollout, and verify one API Pod on each application worker.

Do not remove the worker taints, weaken required placement to every node, or move the API onto the control plane.
Explain why adding only a toleration would not guarantee placement in the intended pool.
