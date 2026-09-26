# A request reserves scheduling capacity

The scheduler compares a Pod's resource requests with available allocatable capacity on candidate nodes.
A request is not a measurement of current usage.
A mostly idle container requesting 99 CPUs can remain Pending because no node can satisfy its declared scheduling requirement.
A limit is a runtime constraint: CPU use can be throttled, while exceeding an enforced memory limit can lead to an OOM kill.
Requests and limits have different roles even when their numbers happen to match.

For CPU, 1000m equals one CPU unit.
For memory, Mi and Gi are binary units, while M and G are decimal units.
Read quantities carefully before diagnosing a capacity problem.
The supplied API uses a modest 50m CPU and 64Mi memory request with a 300m CPU and 192Mi memory limit.
These values are a local exercise budget, not a production sizing recommendation.

Kubernetes classifies Pods into QoS classes based on their configured resources.
The supplied API is Burstable because its CPU and memory requests differ from its limits.
QoS influences eviction behavior under node pressure; it does not make a workload immune to failure.
Use measurements and load testing to choose production values.

## Admission operates before scheduling

A LimitRange can supply defaults for containers that omit resources.
A ResourceQuota bounds aggregate namespace requests, limits, and object counts.
An admission rejection and a scheduled Pod becoming unhealthy are different failure stages.
This example supplies a CPU budget and container defaults:

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

Server-side dry-run still invokes relevant admission checks without creating the Pod.
The assessment uses it to observe an oversized request being denied and omitted resources receiving defaults.
It also reads the running API's cgroup limits, connecting declared intent to Linux enforcement.
