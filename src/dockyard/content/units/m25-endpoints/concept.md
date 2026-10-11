## What a Pod can reach on its node

A Pod runs on a node, and by default its network traffic can go anywhere the node's network goes.
That includes two places that belong to the node, not to any application.

The first is the **instance metadata service**.
Cloud providers run it at the special address `169.254.169.254` on every virtual machine.
Programs on the machine ask it for facts about the machine and, importantly, for short-lived credentials that carry the machine's cloud permissions.
A Pod that can reach it can often borrow those permissions, which is how many real cluster breaches began.
This lab has no cloud, so Dockyard runs a practice stand-in at the same address on each node, serving a harmless fake credential.

The second is the **kubelet API** on port 10250 of every node, which you secured in the previous lesson.
Even with authentication on, there is no reason for an ordinary application Pod to connect to it, and an unreachable endpoint cannot be attacked at all.

```figure
node-endpoints
```

## See the exposure

The `frontend` namespace holds two client Deployments, `trusted-client` and `untrusted-client`.
Ask one of them to fetch the practice credential:

```sh
kubectl exec -n frontend deploy/untrusted-client -- python -c "import urllib.request; print(urllib.request.urlopen('http://169.254.169.254/latest/meta-data/iam/security-credentials/node-role', timeout=3).read().decode())"
```

The fake credential prints.
Find the nodes' addresses with `kubectl get nodes -o wide`; the `INTERNAL-IP` column lists the addresses where each kubelet listens on port 10250.

## Egress policies are allowlists

A **NetworkPolicy** selects Pods and lists the traffic they may send or receive.
You used ingress rules earlier in the course; this lesson uses **egress** rules, which control traffic leaving the selected Pods.

Once a policy with `policyTypes: [Egress]` selects a Pod, that Pod may send only what some rule allows.
The supplied `frontend-egress.yaml` has a single rule, `- {}`, which allows everything, so it protects nothing.
Replace it with rules for exactly what the clients need:

- **DNS**: Pods look up Service names through CoreDNS, which runs in `kube-system` with the label `k8s-app: kube-dns`, on port 53 over UDP and TCP.
- **The Dispatch API**: Pods labelled `app: dispatch` in the `dispatch` namespace, on port 8080.

```figure
egress-allowlist
```

Within one rule, `namespaceSelector` and `podSelector` written in the same list item must both match, which means "these Pods in that namespace".
Written as two separate list items, they would mean "any Pod in that namespace, or these Pods in any namespace", a common and much wider mistake.
Rules talk to the Pod port, 8080, not a Service port, because policies are checked after Service addresses are translated.

Traffic to the metadata address and to the nodes matches no rule, so it is dropped.
You could instead allow everything except certain addresses with an `ipBlock` rule using `except`, but an allowlist also stops destinations you have not thought of.

## Fix it

1. Edit `frontend-egress.yaml` so it allows only DNS and the Dispatch API, as described above.
2. Apply it with `kubectl apply -f frontend-egress.yaml`.
3. Repeat the metadata request from both clients; it should now time out.
4. Confirm the trusted client still reaches Dispatch: `kubectl exec -n frontend deploy/trusted-client -- python -c "import urllib.request; print(urllib.request.urlopen('http://dispatch.dispatch.svc.cluster.local:8080/healthz', timeout=3).read().decode())"`.

## If something goes wrong

- **The trusted client cannot reach Dispatch**: check the DNS rule first; without it, the name `dispatch.dispatch.svc.cluster.local` cannot be looked up at all. Then check the Dispatch rule uses port 8080 and both selectors sit in one list item.
- **The metadata request still succeeds**: an `egress` rule with an empty `to`, or a `- {}`, still allows everything. `kubectl describe networkpolicy -n frontend frontend-egress` shows how Kubernetes read your rules.
- **Only one client is blocked**: the policy's `podSelector` must be `{}` to select every Pod in the namespace.
