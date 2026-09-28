## Surviving the loss of a control-plane node

With one control-plane node, losing that machine means losing the API.
A **highly available (HA)** control plane runs several control-plane nodes, so the cluster keeps working if one fails.
This lab has three control-plane VMs and one worker.

## Quorum: why three, not two

Each control-plane node here runs its own **etcd** member, the database that stores every Kubernetes object.
This layout, with etcd on the control-plane nodes themselves, is called **stacked etcd**; the alternative is **external etcd** on separate machines.

etcd only accepts a change when a **majority** of its members agree, called a **quorum**:

| Members | Majority needed | Failures tolerated |
| --- | --- | --- |
| 1 | 1 | 0 |
| 2 | 2 | 0 |
| 3 | 2 | 1 |
| 5 | 3 | 2 |

Two members are no better than one, which is why HA clusters use odd numbers.
Removing a failed member just to make a health report look tidy changes the cluster’s safety, so do not do it here.

## One address for clients

Clients should not have to know which control-plane node is alive.
They use one stable address, usually a **load balancer** in front of all the API servers.
Here that is **HAProxy** running on the worker VM.
HAProxy checks each API server and only forwards connections to healthy ones.

A healthy etcd majority does not help if the load balancer only knows about the failed server.
That is exactly this lab’s problem.

## What is broken

On the primary control-plane VM, the API server and etcd manifests have been moved out of `/etc/kubernetes/manifests`, so the kubelet stopped them.
The VM and its kubelet are still running, and the other two control-plane nodes still have quorum.
But HAProxy’s configuration lists only the primary, so every request fails.
From your lab terminal, `kubectl` reports something like “Unable to connect to the server: EOF”: HAProxy accepts the connection, finds no healthy server to pass it to, and closes it.
Leave the primary broken: the point is to prove the cluster works *without* it.

The primary node may show NotReady, which is fine.
DNS and Dispatch have been placed so that they keep running on the surviving nodes.

## Worked example: inspect before changing

```sh
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo cat /etc/haproxy/haproxy.cfg
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo journalctl -u haproxy -n 20 --no-pager
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl ps
python -m dockyard.native lb-config > haproxy.cfg
cat haproxy.cfg
```

The helper writes a correct HAProxy configuration for this lab’s machines; it does not install it.
Each `server` line names one API server and turns on health checks with `check`.

To install it on the worker, validate it, and reload HAProxy:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo tee /etc/haproxy/haproxy.cfg < haproxy.cfg > /dev/null
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo haproxy -c -f /etc/haproxy/haproxy.cfg
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo systemctl reload haproxy
```

`haproxy -c` checks the file for mistakes before you reload.

## Proving it works

`kubectl get --raw=/readyz` checks the API is ready.
Check work goes further: it writes, reads, and deletes a ConfigMap through the load balancer, asks the two surviving etcd members if they are healthy, and runs a real job.

This proves the cluster survived losing one control-plane node.
It does not make the whole system highly available: the load balancer, the database volume, and your computer are each still a single point of failure.

## In the exam

Building an HA control plane with kubeadm uses a shared endpoint and shares certificates between control-plane nodes:

```sh
sudo kubeadm init --control-plane-endpoint=LB_ADDRESS:6443 --upload-certs --pod-network-cidr=10.244.0.0/16
sudo kubeadm join LB_ADDRESS:6443 --token ... --discovery-token-ca-cert-hash sha256:... --control-plane --certificate-key ...
```

`--upload-certs` stores the certificates temporarily in the cluster, encrypted, and `--certificate-key` lets another control-plane node fetch them when it joins with `--control-plane`.
