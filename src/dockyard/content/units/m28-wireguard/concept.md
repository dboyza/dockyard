## Traffic between nodes

When a Pod on one node talks to a Pod on another, the packets cross the network between the nodes.
In this cluster, Calico wraps them in **VXLAN**, an encapsulation that carries Pod packets inside ordinary UDP packets between node addresses.
Encapsulation is not encryption: anyone who can watch that network, such as another machine on the same segment or a compromised switch, can read every request and response.

**Pod-to-Pod encryption** protects that path.
There are two common approaches:

- **Node-to-node encryption** in the network plugin. Calico and Cilium can both encrypt all traffic between nodes with **WireGuard**, a modern, fast encrypted tunnel built into the Linux kernel. Applications change nothing.
- **Mutual TLS in a service mesh**, such as Istio or Linkerd. A proxy beside each Pod encrypts each connection and also proves each side's identity, at the cost of running and managing the mesh.

This lesson uses Calico's WireGuard support, because Calico is already the network plugin here.

```figure
wireguard-tunnel
```

## How Calico's WireGuard works

When WireGuard is enabled, Calico's agent on each node, `calico-node`, does three things:

1. It creates a network interface called `wireguard.cali`.
2. It generates a key pair, keeps the private key on the node, and publishes the public key as an annotation on the node's Kubernetes object.
3. It routes Pod traffic for other nodes through `wireguard.cali`, encrypted with the destination node's public key.

Traffic between Pods on the same node never leaves the node and is not affected.

## Turning it on

Calico reads its settings from a **FelixConfiguration** object named `default`.
Felix is the part of `calico-node` that programs routes and policy.
Enable WireGuard there:

```sh
kubectl patch felixconfigurations.crd.projectcalico.org default --type=merge -p '{"spec":{"wireguardEnabled":true}}'
```

Calico picks up the change within a few seconds on every node; nothing needs restarting.

## Checking it worked

The public keys appear on the nodes:

```sh
kubectl get nodes -o custom-columns='NAME:.metadata.name,WIREGUARD:.metadata.annotations.projectcalico\.org/WireguardPublicKey'
```

The interface appears on each node, with byte counters that grow as Pods talk across nodes:

```sh
limactl shell "$DOCKYARD_WORKER" ip -s link show wireguard.cali
```

```figure
wireguard-check
```

## Fix it

1. Look at the worker's interfaces with `limactl shell "$DOCKYARD_WORKER" ip link`; there is no `wireguard.cali` yet.
2. Enable WireGuard in the `default` FelixConfiguration.
3. Confirm both nodes have a public key annotation and a `wireguard.cali` interface.
4. Submit a job through Dispatch, or just wait for the frontend to make requests, and watch the worker's `wireguard.cali` byte counters grow.

## If something goes wrong

- **No `wireguard.cali` appears**: check the patch landed with `kubectl get felixconfigurations.crd.projectcalico.org default -o yaml`, and read `kubectl logs -n kube-system -l k8s-app=calico-node --tail=30` for WireGuard errors.
- **Jobs stop completing**: cross-node traffic is failing in the tunnel, often because of the packet size. Calico adjusts it automatically; give it a minute, then check the `calico-node` logs.
- **The counters do not grow**: the traffic you are watching may be between Pods on the same node. The frontend runs on the control plane and Dispatch on the worker, so their traffic always crosses.
