## A Service name and its route are different mechanisms

CoreDNS answers queries for Kubernetes Service names by observing API objects.
Kube-proxy observes Service and EndpointSlice state and programs each node's data plane.
A DNS response can contain the correct ClusterIP while connections to that IP fail.
Conversely, an old ClusterIP route can continue forwarding after the agent that programmed it stops.
Always identify which layer your test actually exercises.

This fixture contains two faults: the CoreDNS Kubernetes plugin serves the wrong cluster zone, and kube-proxy's rollout selects an unavailable local image.
The new image cannot start, but existing kernel rules can outlive the old process.
A test against only a familiar Service can therefore miss the second failure.

## Worked example: inspect each control loop

```sh
kubectl get configmap coredns -n kube-system -o yaml
kubectl logs deployment/coredns -n kube-system --tail=30
kubectl get daemonset kube-proxy -n kube-system
kubectl get pods -n kube-system -l k8s-app=kube-proxy -o wide
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
```

Compare the configured Kubernetes zone with the `cluster.local` suffix used by workload resolvers.
The fixture saved the original CoreDNS text in `Corefile.original` before introducing the mismatch.
Use it as a configuration comparison, then restore the intended zone and restart CoreDNS so the correction is observed promptly.
CoreDNS can run successfully while serving the wrong zone; a Running status is insufficient.

Inspect kube-proxy's desired image and each Pod's events separately.
The reference version for this cluster is `registry.k8s.io/kube-proxy:v1.35.8`, already cached by native cluster bootstrap.
Repair the DaemonSet's image and wait for its rollout on both nodes.
Changing the host's kubectl binary cannot repair a guest data-plane agent.

## Test new state, not only old state

Use a newly named diagnostic Service so the route cannot simply be left over from before the failure.
Resolve the new name from the trusted frontend, compare the answer with the Service's actual ClusterIP, and request that numeric address separately.
If DNS fails but the numeric address works, investigate the resolver path.
If DNS succeeds but the numeric address fails, inspect endpoints and Service programming before rewriting the Corefile again.

The assessment creates and removes its own uniquely named Service selecting the existing API Pods.
For this isolated network diagnostic it publishes not-ready addresses and requests `/healthz`, so a database-readiness failure does not masquerade as a missing packet route.
That temporary probe does not change the readiness behavior of the learner's real Dispatch Service.
A separate fresh job check still requires the complete application, database, and queue to function.
