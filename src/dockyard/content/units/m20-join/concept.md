## Adding a worker and a Pod network

The control plane is running on one machine.
In this lesson you add the worker machine and install the Pod network, then deploy Dispatch across both.

## How a worker joins

A running kubelet is not enough to make a machine part of a cluster.
`kubeadm join` does three things:

1. It contacts the API server and checks it is the right cluster, using a **CA certificate hash**. This stops a worker joining an impostor.
2. It proves the worker is allowed to join, using a short-lived **bootstrap token**.
3. It gives the worker’s kubelet its own permanent credentials.

The token is a secret; the hash is a fingerprint of the cluster’s CA.
Skipping the hash check (`--discovery-token-unsafe-skip-ca-verification`) removes that protection and is never the fix for a wrong address.

## Worked example

Before joining, only the control plane is in the cluster:

```sh
kubectl get nodes -o wide
kubectl get pods -n kube-system -o wide
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" systemctl status kubelet --no-pager
```

Generate a join configuration for this lab’s worker, use it, and delete it:

```sh
umask 077
python -m dockyard.native join-config "$DOCKYARD_WORKER" > join.yaml
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo kubeadm join --config=/dev/stdin < join.yaml
rm join.yaml
```

`umask 077` makes new files readable only by you.
Deleting the file reduces the chance of leaking it, but the token stays valid until it expires.

## Installing the Pod network

A **CNI plugin** gives every Pod an address and carries traffic between nodes.
This lab uses Calico, set up for the `10.244.0.0/16` Pod range and **VXLAN**, which wraps Pod traffic inside ordinary packets between the VMs.

```sh
python -m dockyard.native network-manifest > calico.yaml
kubectl apply -f calico.yaml
kubectl wait --for=condition=Ready nodes --all --timeout=240s
kubectl rollout status daemonset/calico-node -n kube-system --timeout=240s
kubectl rollout status deployment/coredns -n kube-system --timeout=240s
sh bootstrap.sh
```

Read `calico.yaml` before applying it; it is a large file, but look for the Pod range.
Once Calico runs on each node, the nodes turn Ready and CoreDNS starts.
`bootstrap.sh` then deploys Dispatch, with its frontend on the control plane and its API on the worker, so a request must cross between machines.

Ready nodes are not proof that networking works.
A new job travelling from the frontend, through Service DNS, to the API, queue, worker, and database is.

## In the exam

On a real control plane, you create a join command with:

```sh
kubeadm token create --print-join-command
```

It prints a complete `kubeadm join HOST:6443 --token ... --discovery-token-ca-cert-hash sha256:...` command to run, with `sudo`, on the new worker.
`kubeadm token list` shows existing tokens and when they expire.
