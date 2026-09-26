# Scaling follows a feedback loop

The HorizontalPodAutoscaler reads metrics, compares them with a target, and updates the scale of a workload.
For CPU utilization, the percentage is measured use divided by the resource request, so meaningful requests are part of the control loop.
A target of 50 percent of a 50m request is 25m of average CPU use per Pod.
Missing requests, unavailable metrics, an incorrect target reference, or exhausted capacity can prevent the expected outcome.

The lab supplies Metrics Server with verified TLS to both kubelets and the Kubernetes aggregation endpoint.
The workload still needs a correct autoscaling/v2 HPA.
Dispatch has a bounded CPU-work endpoint and a supplied local load generator that sends real HTTP requests.
With this load active, the exercise expects the HPA to request four replicas within its configured two-to-four range.

```sh
kubectl top nodes
kubectl top pods
kubectl describe hpa dispatch
kubectl get hpa dispatch -w
kubectl get deployment dispatch -w
```

Read AbleToScale, ScalingActive, and ScalingLimited conditions alongside current and desired replicas.
ScalingLimited can be true because the controller reached maxReplicas while demand remains high; that is not automatically a broken metrics pipeline.
Stabilization and control-loop intervals mean scaling is not instantaneous.

A PodDisruptionBudget constrains voluntary eviction, such as a drain using the eviction API.
For this service, minAvailable 2 protects two healthy replicas during planned worker maintenance.
It does not prevent hardware failure, force application health, or replace the Deployment rollout strategy.
Overly strict budgets can legitimately block a drain.

## Eviction and request draining are separate

EndpointSlice updates and process termination proceed asynchronously when a Pod is deleted.
The supplied API has a five-second preStop sleep within its twenty-second termination grace period, allowing endpoint routing changes to propagate before SIGTERM closes the server.
This is a measured local drain allowance, not a guarantee for arbitrary load balancers or long-lived connections.
A PDB constrains the number of voluntary evictions; it does not drain individual network requests.
After replacement, the rehearsal also waits for Metrics Server to observe the new Pod identities before assessing scaling.
See the [official termination flow](https://kubernetes.io/docs/tutorials/services/pods-and-endpoint-termination-flow/) for the relationship between terminating endpoints and serving traffic.
