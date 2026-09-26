# Replace an impossible request with an observed budget

Both API replicas request and limit 99 CPUs, leaving them unschedulable.
Inspect Pod events and node allocatable resources before editing `platform.yaml`.
Use the supplied API request/limit values, render and apply the corrected platform, and wait for two available replicas.

Then add the LimitRange and ResourceQuota from the example to `capacity.yaml`, preserving its existing disruption budget, and apply it.
Repair the oversized Pods before imposing the tighter aggregate quota so their old requests do not block replacement admission.
Inspect `kubectl describe quota dispatch-budget` and `kubectl get pods -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass`.
Explain the difference between a request that prevents scheduling and a running process that exceeds a limit.
