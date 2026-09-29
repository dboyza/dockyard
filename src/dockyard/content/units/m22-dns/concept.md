## Two different jobs: naming and routing

When a Pod connects to `dispatch:8080`, two separate systems are involved:

1. **CoreDNS** turns the name into the Service’s ClusterIP. It reads Services from the API.
2. **kube-proxy**, running on every node, programs the node’s networking so traffic to that ClusterIP reaches one of the Service’s Pods.

Either can fail on its own.
DNS can return the right IP while nothing routes it; and routes kube-proxy already set up keep working after it stops, until something changes.

## This lab

Two things are broken:

- CoreDNS is configured for the wrong **cluster domain**, so names ending in `cluster.local` are not answered.
- kube-proxy’s DaemonSet was changed to an image that does not exist, so its new Pods cannot start.

Because old routes survive, an existing Service may still work.
That is why you test with a **brand-new** Service, which needs a running kube-proxy to route it.

## Worked example: check each system

```sh
kubectl get configmap coredns -n kube-system -o yaml
kubectl logs deployment/coredns -n kube-system --tail=30
kubectl get daemonset kube-proxy -n kube-system
kubectl get pods -n kube-system -l k8s-app=kube-proxy -o wide
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
```

CoreDNS’s settings live in the `coredns` ConfigMap, in a file called the **Corefile**.
Its `kubernetes` line names the cluster domain it answers for; it should be `cluster.local`.
The lab saved the original as `Corefile.original` in your workspace so you can compare.
You can fix it with `kubectl edit configmap coredns -n kube-system`, or rebuild it from the saved file:

```sh
kubectl create configmap coredns -n kube-system --from-file=Corefile=Corefile.original --dry-run=client -o yaml | kubectl apply -f -
```

kubectl may warn about a missing “last-applied-configuration” annotation the first time; that is harmless.
After fixing the ConfigMap, run `kubectl rollout restart deployment/coredns -n kube-system` so CoreDNS picks it up quickly.
CoreDNS can be Running while answering for the wrong domain, so its status alone proves nothing.

For kube-proxy, compare the DaemonSet’s image with what its Pods report in their events.
The correct image is `registry.k8s.io/kube-proxy:v1.35.8`, already cached on the nodes:

```sh
kubectl set image daemonset/kube-proxy -n kube-system kube-proxy=registry.k8s.io/kube-proxy:v1.35.8
kubectl rollout status daemonset/kube-proxy -n kube-system
```

## Which resolver a Pod uses

Each Pod’s `dnsPolicy` decides where its DNS questions go.
`ClusterFirst`, the normal setting for Pods, sends them to CoreDNS, so Service names work.
Confusingly, `Default` means “use the node’s own resolver”, which knows nothing about Services.
You can see a Pod’s settings with `kubectl exec POD -- cat /etc/resolv.conf`.

## Test new state

Create a new test Service, look up its name from the trusted frontend, compare the answer with the Service’s real ClusterIP, and request that IP directly:

- DNS fails but the IP works: look at CoreDNS.
- DNS works but the IP fails: look at kube-proxy and the endpoints.

Check work does exactly this with a temporary Service of its own, using `/healthz` so a database problem cannot be mistaken for a routing problem, and then runs a real job.
