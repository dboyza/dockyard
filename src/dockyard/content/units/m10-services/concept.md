## Three ways to reach Dispatch

Pods come and go, and each new Pod gets a new IP address.
A **Service** gives clients one stable name and address that always leads to whichever matching Pods are ready.
You met one in module 7; now you’ll look at the three common **types** of Service and when each is used.

| Type | Reachable from | Typical use |
| --- | --- | --- |
| **ClusterIP** (the default) | inside the cluster only | one app calling another, such as the API calling PostgreSQL |
| **NodePort** | a fixed port on every node | simple testing, or behind your own load balancer |
| **LoadBalancer** | an address given out by a load balancer | exposing an app to users outside the cluster |

Each type builds on the one before: a NodePort Service also has a ClusterIP, and a LoadBalancer Service also has a NodePort.

## Ports: three numbers that are easy to mix up

```yaml
ports:
- port: 8080
  targetPort: 8080
  nodePort: 30080
```

- `port` is what clients of the Service connect to.
- `targetPort` is where the application listens inside the Pod. It must match the real listener, which for Dispatch is 8080.
- `nodePort`, for NodePort and LoadBalancer Services, is the port opened on every node, normally between 30000 and 32767.

A container’s `containerPort` in the Deployment is only a label; it does not make the application listen anywhere.
If `targetPort` is wrong, the Service still has endpoints but every connection fails.

## Endpoints tell you what the Service really reaches

```sh
kubectl get services
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
kubectl get pods -l app=dispatch -o wide
```

The EndpointSlice lists the Pod IPs and the port the Service sends traffic to.
Compare those IPs with the Pods’ IPs from `-o wide`, and the port with the port Dispatch listens on.

## LoadBalancer needs something to hand out addresses

Creating a LoadBalancer Service asks the cluster for an external address.
In a cloud, the provider creates a real load balancer.
On a local cluster, nothing answers unless you install something that does, and the Service stays `<pending>` forever.
This lab runs **MetalLB**, which hands out addresses on the cluster’s private Docker network.

## Trying each path

**ClusterIP**, from inside the cluster:

```sh
kubectl exec deployment/dispatch -c api -- python -c 'import urllib.request; print(urllib.request.urlopen("http://dispatch:8080/healthz").read().decode())'
```

**NodePort**, from your computer.
This lab connects node port 30080 to `$DOCKYARD_PORT` on your computer:

```sh
curl --fail "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

**LoadBalancer**, from a temporary container on the cluster’s Docker network, playing the part of an outside client:

```sh
LB_IP=$(kubectl get service dispatch-public -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "$LB_IP"
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" --network "$DOCKYARD_NETWORK" "$DOCKYARD_BUSYBOX_IMAGE" wget -qO- "http://$LB_IP:8080/healthz"
```

`-o jsonpath=...` pulls one value out of the Service; here, the address MetalLB assigned.

## Creating Services quickly

`kubectl expose` creates a Service that selects a Deployment’s Pods for you:

```sh
kubectl expose deployment dispatch --name=demo --port=8080 --target-port=8080 --type=NodePort --dry-run=client -o yaml
```

It copies the Deployment’s selector, which avoids label typos.
Remove `--dry-run=client -o yaml` to create it for real.

## Headless Services

A Service with `clusterIP: None` is called **headless**.
Its DNS name returns the Pods’ own addresses instead of one virtual address.
The StatefulSet lesson uses one so each database Pod can be reached by name.

## ExternalName Services

An **ExternalName** Service has no Pods behind it at all.
Its DNS name simply answers with another DNS name, so applications in the cluster can use a stable internal name for something outside it:

```sh
kubectl create service externalname billing --external-name billing.example.com
kubectl get service billing
```

Inside the cluster, `billing` now resolves to `billing.example.com`.
There is no ClusterIP, no port mapping, and no EndpointSlice, so nothing checks that the outside address works.
