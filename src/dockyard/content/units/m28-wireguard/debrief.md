## What changed

Calico now encrypts all Pod traffic between the nodes with WireGuard: each node has its own key pair, publishes its public key on its Node object, and sends traffic for other nodes through `wireguard.cali`.
Dispatch and the frontend changed nothing and noticed nothing.

Check your understanding: two Pods on the same node talk to each other.
Is their traffic encrypted now, and does it need to be?
What does a service mesh's mutual TLS give you that node-to-node encryption does not?
