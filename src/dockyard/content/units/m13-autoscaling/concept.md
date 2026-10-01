## Let Kubernetes add copies when they are busy

When Dispatch gets busy, more API copies can share the work.
A **HorizontalPodAutoscaler (HPA)** does this automatically: it regularly measures the Pods, compares the measurement with a target, and changes the Deployment’s replica count.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dispatch
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dispatch
  minReplicas: 2
  maxReplicas: 4
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

`scaleTargetRef` names what to scale.
The HPA keeps the count between `minReplicas` and `maxReplicas`, aiming for the target.

You can create a simple one from the command line too:

```sh
kubectl autoscale deployment dispatch --min=2 --max=4 --cpu-percent=50
```

## Utilization is measured against the request

CPU utilization is a percentage of the container’s CPU **request**, not of the node.
With a 50m request and a 50% target, the HPA aims for an average of 25m of real CPU use per Pod.
If average use rises to 100m, that is 200% of the request, so the HPA wants about four times as many Pods, up to its maximum.

That is why an HPA cannot work without requests.

```figure
hpa-math
```

## Where the measurements come from

The HPA reads CPU and memory numbers from the **Metrics Server**, which this lab has installed for you.
The same numbers are what `kubectl top` shows:

```sh
kubectl top nodes
kubectl top pods
```

If `kubectl top` fails, the HPA is blind too.

## Watching it decide

```sh
kubectl describe hpa dispatch
kubectl get hpa dispatch -w
kubectl get deployment dispatch -w
```

`describe hpa` shows the current measurement against the target, and three conditions:

- **AbleToScale**: the HPA can change the target’s replica count.
- **ScalingActive**: it is getting metrics and calculating.
- **ScalingLimited**: it wants to go beyond min or max. Hitting `maxReplicas` under heavy load sets this, and that is expected, not a fault.

Scaling takes time: metrics are collected every few seconds, and the HPA waits before scaling down again so it does not bounce up and down.

This lab includes a load generator that sends real requests to Dispatch’s `/work` address, which uses CPU on purpose.
With it running, the HPA should settle at four replicas.
Stop the lab when you are done, so the load generator stops using your computer’s CPU.

## Protecting capacity during maintenance

A **PodDisruptionBudget (PDB)** limits how many Pods of an application planned operations may remove at once.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: dispatch
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: dispatch
      track: stable
```

`kubectl create pdb dispatch --selector=app=dispatch,track=stable --min-available=2` creates the same thing.

A PDB applies to **voluntary** disruptions, such as `kubectl drain` evicting Pods before node maintenance.
It cannot stop a node crashing, and it cannot create spare capacity.
A budget that allows no disruption at all will block every drain.

```figure
pdb-drain
```

## Letting in-flight requests finish

When a Pod is removed, two things happen at the same time: Services stop sending it new traffic, and the container receives SIGTERM.
If the process exits instantly, requests still on their way can fail.
Dispatch’s Deployment has a short `preStop` hook, `sleep 5`, which gives the Service change time to spread before SIGTERM arrives, within its twenty-second grace period.
The [official termination flow](https://kubernetes.io/docs/tutorials/services/pods-and-endpoint-termination-flow/) explains this in detail.

```figure
prestop-timeline
```
