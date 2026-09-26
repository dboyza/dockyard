# A policy declaration needs an enforcing data plane

NetworkPolicy selects Pods and describes allowed ingress, egress, or both.
The installed Calico CNI enforces those rules in the actual practice cluster.
Simply creating a NetworkPolicy object on an unsupported CNI would not establish isolation.
Policies are additive: a broad allow policy can reopen traffic even when a default-deny policy also exists.

The Dispatch namespace starts with ingress and egress isolation for every Pod.
Separate rules allow DNS, API access from the trusted frontend, API and worker access to PostgreSQL and Redis, and the inventory process's Kubernetes API connection.
Replies to an allowed connection do not need a separate reverse connection rule.
New reverse connections are different and must satisfy the applicable policies.

A peer with namespaceSelector and podSelector in the same list item requires both to match.
Putting them in separate list items creates alternatives.
For an unrelated reporting service, this peer allows only reporter Pods in the analytics namespace:

```yaml
from:
- namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: analytics
  podSelector:
    matchLabels:
      app: reporter
```

A podSelector without a namespaceSelector selects peers in the policy's own namespace.
An empty selector selects all Pods in its scope; it is not a denial by itself.
A default-deny policy isolates selected Pods by declaring a direction with no allowed rules.
An empty ingress rule, written ingress: [{}], instead allows all ingress for those Pods.

DNS normally uses UDP but can also require TCP.
The allow-dns policy explicitly permits both protocols on port 53 to CoreDNS Pods in kube-system.
The checker performs real UDP and TCP DNS requests rather than accepting a YAML port list as proof.
It also checks an allowed frontend, a wrong Pod label, and the correct Pod label in the wrong namespace across two nodes.

```sh
kubectl get networkpolicy
kubectl describe networkpolicy allow-business-reads
kubectl get pods -n frontend -o wide
kubectl get pods -l app=dispatch -o wide
```

A failed connection is meaningful only when a positive control shows the destination is reachable from an allowed peer.
The egress target in dockyard-observer remains reachable from the frontend while the API is denied access to it.
The API can reach the database while a frontend client cannot.
These tests distinguish policy enforcement from a down service or broken DNS.
NetworkPolicy does not replace TLS, application authentication, RBAC, or host isolation.
Its treatment of node-origin traffic and address translation requires care; this exercise measures Pod-to-Pod traffic explicitly.
