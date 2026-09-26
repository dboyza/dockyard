# Restore the reconciler and prove drift repair

The CRD and WorkerPool exist, but the controller Deployment starts with zero replicas.
Inspect the custom resource, controller identity, and generated Deployment ownership.
Set the controller to one replica in `operator.yaml`, render and apply it, and wait for the WorkerPool Ready condition.
The pool requests two workers; the ordinary worker Deployment is intentionally scaled to zero.
Run `python operator-proof.py` to perturb the generated worker count and observe recovery.
Keep the owner reference and namespaced RBAC intact.
The assessment submits a unique Dispatch job and verifies that the operator-owned workers actually complete it.
