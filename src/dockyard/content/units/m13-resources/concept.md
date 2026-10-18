## Tell Kubernetes what each container needs

Every node has a limited amount of CPU and memory.
To place Pods sensibly, and to stop one container starving the others, Kubernetes lets each container state two amounts:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 300m
    memory: 192Mi
```

- A **request** is what the container is guaranteed. The scheduler only places a Pod on a node with enough unreserved room for all its requests.
- A **limit** is the most it may use. Going over the CPU limit slows the container down (**throttling**); going over the memory limit gets it killed (**OOMKilled**, out of memory).

Requests are about *reservation*, not actual use.
A container that does nothing but requests 99 CPUs can never be scheduled on a smaller node.

```figure
requests-limits
```

## Units

| Written | Means |
| --- | --- |
| `1` or `1000m` CPU | one whole CPU core |
| `250m` CPU | a quarter of a core ("m" means thousandths) |
| `64Mi` memory | 64 mebibytes (64 × 1024 × 1024 bytes) |
| `64M` memory | 64 megabytes (64 × 1000 × 1000 bytes) |

`Mi` and `M` are easy to mix up; the difference grows with size.

## Quality of service

From its requests and limits, Kubernetes puts each Pod in a **QoS class**:

- **Guaranteed**: every container has requests equal to limits for both CPU and memory.
- **Burstable**: at least one request or limit is set, but not in the Guaranteed way.
- **BestEffort**: no requests or limits at all.

When a node runs short of memory, BestEffort Pods are evicted first and Guaranteed Pods last.
Dispatch’s API is Burstable, because its requests are lower than its limits.

```figure
qos-classes
```

## Seeing what a node has

```sh
kubectl describe node NODE_NAME
kubectl describe pods -l app=dispatch,track=stable
```

In `describe node`, **Allocatable** is what Pods may use, and **Allocated resources** shows how much is already requested.
A Pod that cannot fit stays `Pending` with a `FailedScheduling` event such as “Insufficient cpu”.

## Rules for a whole namespace

Two objects let an administrator set rules before Pods are even created. This checking step is called **admission**.

- A **LimitRange** gives default requests and limits to containers that do not set their own, and can set minimums and maximums.
- A **ResourceQuota** caps the total that everything in a namespace may request, and can cap object counts too.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: dispatch-defaults
  namespace: dispatch
spec:
  limits:
  - type: Container
    defaultRequest: {cpu: 50m, memory: 64Mi}
    default: {cpu: 500m, memory: 256Mi}
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dispatch-budget
  namespace: dispatch
spec:
  hard:
    requests.cpu: '2'
    requests.memory: 2Gi
    limits.cpu: '6'
    limits.memory: 6Gi
    pods: '24'
```

A Pod that would break the quota is rejected with an error when you create it.
That is a different failure from a Pod that is created but cannot be scheduled.
`kubectl create quota` can also create simple quotas from the command line.

```sh
kubectl describe quota dispatch-budget
kubectl get pods -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass
```

Order matters in this lab: fix the oversized Pods *before* adding the quota, or their huge old requests will count against it and block the replacements.

The values used here are a small practice budget.
Real values come from measuring the application under realistic load.
