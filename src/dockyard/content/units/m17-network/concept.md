## Deciding which Pods may talk to which

By default, every Pod in a cluster can connect to every other Pod.
A **NetworkPolicy** narrows that down: it picks some Pods and says which traffic they may receive (**ingress**) or send (**egress**).
Policies are enforced by the cluster’s network plugin; this lab uses Calico, which supports them.
On a plugin without NetworkPolicy support, the objects are accepted and silently do nothing.

## How policies combine

- A Pod not selected by any policy allows all traffic.
- Once a policy selects a Pod for a direction, only traffic some policy allows in that direction gets through. The Pod is **isolated** for that direction.
- Policies only ever add permissions. There is no “deny” rule; if two policies select a Pod, traffic allowed by either gets through.
- Replies to an allowed connection are allowed automatically.

A **default-deny** policy selects every Pod and allows nothing:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```

`podSelector: {}` means “every Pod in this namespace”.
With `policyTypes` listed and no rules, nothing is allowed.
Be careful: `ingress: [{}]`, a rule with nothing in it, means the opposite: allow all ingress.

```figure
netpol-default-deny
```

## Allowing specific traffic

```yaml
spec:
  podSelector:
    matchLabels: {app: dispatch}
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: frontend
      podSelector:
        matchLabels:
          app: trusted
    ports:
    - protocol: TCP
      port: 8080
```

This lets Pods labeled `app: trusted` **in** the `frontend` namespace reach Dispatch on port 8080.

The indentation of the `from` list is the single most common NetworkPolicy mistake:

- `namespaceSelector` and `podSelector` in the **same** list item (one `-`) must **both** match.
- In **separate** list items (two `-`), **either** one is enough.

A `podSelector` with no `namespaceSelector` means Pods in the policy’s own namespace.
Every namespace automatically has the label `kubernetes.io/metadata.name` set to its name, which makes it easy to select.

```figure
netpol-and-or
```

## Don’t forget DNS

Once egress is denied, Pods cannot even look up names.
Allow traffic to the cluster’s DNS Pods (CoreDNS, in `kube-system`) on port 53, over **both UDP and TCP**.
DNS usually uses UDP but falls back to TCP for larger answers, and allowing only UDP causes confusing, intermittent failures.

## This lab

The `dispatch` namespace starts with ingress and egress denied for every Pod.
Rules then allow DNS, and let the trusted frontend reach the API.
Other rules let the API and workers reach PostgreSQL and Redis, and let the inventory Pod reach the Kubernetes API.

```sh
kubectl get networkpolicy
kubectl describe networkpolicy allow-business-reads
kubectl get pods -n frontend -o wide --show-labels
kubectl get pods -l app=dispatch -o wide
```

## Testing a policy properly

A blocked connection only means something if you also show that an allowed connection works.
Otherwise you cannot tell a working policy from a broken service.
Check work tests a whole set of paths, across two nodes:

- the trusted frontend reaches the API (must work);
- an untrusted frontend Pod, and a trusted-looking Pod in the wrong namespace, cannot;
- DNS works over both UDP and TCP;
- the frontend cannot reach the database;
- the API cannot reach an outside test target that the frontend *can* reach.

NetworkPolicy controls which connections are allowed.
It is not encryption, and it does not check who a user is.
Traffic from the nodes themselves can behave differently, which is why this lab only tests Pod-to-Pod traffic.
