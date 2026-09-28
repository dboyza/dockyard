# Names and DNS

Computers find each other by numeric addresses such as `10.96.0.10`.
People and programs prefer names such as `dispatch`.
**DNS**, the Domain Name System, is the service that turns names into addresses.
This is called **resolving** a name.

## A name is not a working service

Resolving a name only gives you an address.
It does not tell you whether anything is listening there, whether traffic is allowed through, or whether the application works.
When a request fails, check the name first, then the connection, then the application, one step at a time.

## Short names depend on where you ask from

In Docker Compose, each service name, such as `db`, works as a name for containers on the same project network.

In Kubernetes, a Service named `dispatch` in the `dispatch` namespace has a full name of `dispatch.dispatch.svc.cluster.local`.
Programs usually use the short name `dispatch`, and the Pod’s DNS settings fill in the rest.
That shortcut assumes the same namespace.
From a Pod in a different namespace, use at least `dispatch.dispatch`.

Your own computer does not use the cluster’s DNS, so these names only work from inside the cluster.

## Looking a name up

From inside a Pod, you can check what a name resolves to:

```sh
nslookup kubernetes.default.svc.cluster.local
cat /etc/resolv.conf
```

`nslookup` asks DNS for a name and prints the answer.
`/etc/resolv.conf` shows which DNS server the Pod uses and which search suffixes it adds to short names.

Some images do not include `nslookup`.
“Command not found” means the tool is missing, not that DNS is broken; try a different image or a small Python one-liner instead.

## How a request reaches a Service

1. The program resolves the Service’s name. For a normal Service, DNS returns one stable virtual address, the **ClusterIP**.
2. Kubernetes forwards traffic sent to that address to one of the ready Pods the Service has selected, called its **endpoints**.
3. That Pod’s application handles the request.

So a Service name can resolve perfectly while the Service has no ready endpoints behind it, and every request still fails.

A **headless** Service has no ClusterIP; DNS returns the Pods’ own addresses instead.
StatefulSets use this so each Pod has its own name.

## Network policies can block DNS too

A network policy that blocks all outgoing traffic also blocks DNS lookups.
DNS uses port 53 over UDP, and sometimes TCP.
If you allow a Pod to reach its database port but not DNS, it still cannot find the database by name.

## DNS needs to stay available

DNS in a cluster is provided by Pods, usually CoreDNS.
Several CoreDNS copies all on one node stop together if that node fails, so spreading them across nodes matters.
The high-availability lesson explores this.

## Check your understanding

A Service name resolves, but connecting to it fails.
Why is changing the name not yet the right fix, and what would you check next?
