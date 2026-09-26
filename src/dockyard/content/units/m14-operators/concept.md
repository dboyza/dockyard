# New API objects need a controller to become behavior

A CustomResourceDefinition registers a resource type and its validation schema with the API server.
A WorkerPool object then expresses desired worker count using that type.
Neither object alone starts a worker process.
The supplied controller reads WorkerPools and reconciles an owned Deployment toward their requested count.
This is the operator pattern in a small, inspectable form.

The schema permits replicas from zero through four and exposes a status subresource.
The controller writes status.observedGeneration and a Ready condition for the generation it has processed.
A status value from an older generation is stale evidence even if it says Ready.
The managed Deployment has an owner reference to the exact WorkerPool UID, not just its name.
The controller refuses to adopt a same-named Deployment owned by someone else.

```sh
kubectl get crd workerpools.learning.dockyard.local
kubectl explain workerpool.spec
kubectl get workerpool dispatch -o yaml
kubectl logs deployment/workerpool-controller
kubectl get deployment dispatch-workers -o yaml
```

The controller uses a namespaced service account and Role limited to its resources and Deployments.
It has no cluster-wide administrator credentials.
Application workers have no API token because processing Dispatch jobs does not require Kubernetes API access.

To observe reconciliation, change the managed Deployment to zero replicas while the WorkerPool still requests two.
The supplied operator-proof.py does that bounded experiment, waits for two available workers again, and records both generations and ownership.
Direct changes to generated resources are temporary when a controller keeps reconciling a different source of truth.
For a lasting scale change, edit the WorkerPool.
This teaching controller polls and retries; production operators additionally need mature queueing, leader election, upgrade, deletion, and failure handling.
