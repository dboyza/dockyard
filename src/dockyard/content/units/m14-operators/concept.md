## Teaching Kubernetes a new kind of object

Kubernetes comes with object types such as Pod and Deployment, but you can add your own.
A **CustomResourceDefinition (CRD)** registers a new type with the API server, including a schema describing its fields.
After that, you can create objects of the new type, called **custom resources**, with kubectl like any other.

On its own, a custom resource is just stored data.
Nothing happens until a **controller** watches those objects and acts on them.
A controller that manages an application this way is called an **operator**: it encodes what a human operator would do, and keeps doing it.
This is the same reconciliation idea you met with Deployments, applied to your own object type.

## This lab’s operator

The lab adds a `WorkerPool` type:

```yaml
apiVersion: learning.dockyard.local/v1alpha1
kind: WorkerPool
metadata:
  name: dispatch
spec:
  replicas: 2
```

The supplied controller watches WorkerPools and keeps a Deployment called `dispatch-workers` at the requested size.
Its schema allows 0 to 4 replicas, and the controller reports progress in the WorkerPool’s `status`:

- `status.observedGeneration` says which version of the spec it last acted on. Every spec change increases `metadata.generation`, so if these differ, the status is out of date.
- A `Ready` condition says whether the workers match the request.

The generated Deployment has an **owner reference** pointing at the exact WorkerPool, identified by its UID.
The controller will not take over a Deployment that someone else owns, even if its name matches.

## Looking around

```sh
kubectl get crd workerpools.learning.dockyard.local
kubectl api-resources --api-group=learning.dockyard.local
kubectl explain workerpool.spec
kubectl get workerpool dispatch -o yaml
kubectl logs deployment/workerpool-controller
kubectl get deployment dispatch-workers -o yaml
```

`kubectl explain` works for custom types too, because the CRD’s schema describes their fields.

The controller runs as its own ServiceAccount, with a Role that only lets it manage WorkerPools and Deployments in this namespace.
The workers themselves have no API token, because processing jobs does not need one.

## Drift and the source of truth

If you scale `dispatch-workers` by hand, the controller notices on its next pass and puts it back to what the WorkerPool says.
The WorkerPool is the **source of truth**; to make a lasting change, edit the WorkerPool.
The supplied `operator-proof.py` does exactly this experiment: it scales the generated Deployment to zero, waits for the controller to restore two workers, and records what happened.

```figure
operator-loop
```

This small controller simply polls and retries.
Real operators also handle upgrades, deletion clean-up, running several copies safely, and reporting failures.
