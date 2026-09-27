# Separate names, addresses, and working services

DNS resolves names into records such as IP addresses.
A successful lookup does not prove that a process is listening, that a route is allowed, or that an application is ready.
A name can remain stable while its backing endpoints change.

## The same short name can mean different things

In a Compose project, a service name can resolve through that project's container network.
In Kubernetes, a Service named `dispatch` in namespace `dispatch` has the conventional full name `dispatch.dispatch.svc.cluster.local` in this course's cluster domain.
A short name is expanded using the requesting Pod's DNS search configuration.
A Pod in another namespace may need a namespace-qualified or fully qualified name.
Your host computer does not automatically use the cluster's DNS resolver.

## Inspect before guessing

Inside an appropriate Linux guest or Pod, `/etc/resolv.conf` shows resolver addresses and search domains.
When the image includes the tool, use a lookup such as:

```sh
nslookup kubernetes.default.svc.cluster.local
```

Run it from a Pod in a prepared Kubernetes lab, where cluster DNS is meaningful.
An image lacking `nslookup` has a missing diagnostic tool; that error is not evidence that DNS itself is broken.
The exact lookup tool matters less than observing the requested name, the resolver used, and the returned answer or error.

## Follow a Service request

The client first resolves a Service name.
For an ordinary ClusterIP Service, DNS normally returns the Service's virtual IP.
The Service proxy then directs eligible traffic to ready endpoints selected from matching Pods.
A Service can therefore resolve correctly while having no usable endpoints.
A headless Service deliberately omits that virtual IP and exposes endpoint addresses through DNS, subject to its configuration.
Neither type guarantees that the application responds correctly.

## Policies can block the lookup itself

A default-deny egress policy may block traffic to DNS as well as to the business dependency.
DNS commonly uses UDP 53 and can also require TCP 53.
Allowing only an application port will not help a client that cannot resolve the dependency's name.
Verify both name resolution and the actual intended request from the relevant source workload.
A request from the host computer or a node can follow a different policy path from a request from a Pod.

## DNS availability has placement requirements

Multiple CoreDNS replicas on one failed node do not provide independent availability.
Inspect which nodes run the replicas, whether they are Ready, and whether the DNS Service has usable endpoints.
The HA lesson spreads DNS across control-plane nodes so its deliberate primary outage leaves surviving resolvers.
This is separate from etcd quorum and API load-balancer routing.

## Check your understanding

A Service name resolves, but the client gets a connection error.
Explain why changing the DNS name is not yet a justified repair, and identify the next endpoint and traffic observations you would gather.
