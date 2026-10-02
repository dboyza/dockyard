## Underneath Kubernetes: the container runtime

Kubernetes does not run containers itself.
On every node, the **kubelet** (the node’s Kubernetes agent) asks a **container runtime**, here **containerd**, to start and stop containers.
They talk through a standard interface called the **Container Runtime Interface (CRI)**.

That gives you three different tools that look similar:

| Tool | Talks to | Use it to |
| --- | --- | --- |
| `kubectl` | the Kubernetes API server | see and change Kubernetes objects |
| `crictl` | containerd, through the CRI | see what is really running on one node |
| `ctr` | containerd directly, below the CRI | low-level containerd administration |

`crictl` is the one to know for the CKA.
It finds the runtime through a small config file, `/etc/crictl.yaml`, which names the runtime’s **socket**, a special file used for local connections.
On these nodes that is `/run/containerd/containerd.sock`.
If `crictl` is pointed at the wrong socket it fails, but that does not stop any container: running Pods carry on.

```figure
runtime-layers
```

## cgroups: how Linux limits and tracks containers

Linux **cgroups** group processes so the kernel can measure and limit their resources.
These nodes use cgroup version 2 with the **systemd** cgroup driver, meaning containers are arranged under systemd’s tree, for example under `kubepods.slice`.
A setting in a config file says what *should* happen; finding a real Dispatch process under `kubepods.slice` shows it *is* happening.
Do not change the cgroup driver on a running node just to make a diagnostic command work.

## Worked example: find a component’s real process

Enter the control-plane VM and inspect the API server’s container:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"
sudo crictl info
sudo crictl ps --name kube-apiserver
sudo crictl inspect CONTAINER_ID | grep '"pid"'
sudo cat /proc/PID/cgroup
exit
```

Replace `CONTAINER_ID` with the ID from `crictl ps`, and `PID` with the number from `inspect`.
The container ID, the process ID, and the Pod name are three different names for related things.
`crictl` needs `sudo` because the socket belongs to root.

## Find the broken layer before changing it

If `crictl` cannot connect, the cause could be a wrong socket path in `/etc/crictl.yaml`, containerd not running, or containerd running but unhealthy.
Check them in that order:

```sh
sudo cat /etc/crictl.yaml
systemctl is-active containerd
kubectl get nodes
```

The last one, run from your lab terminal, tells you whether Kubernetes still sees the node as healthy.

## Working in this lab’s machines

From this module on, Dispatch runs on two real Ubuntu virtual machines, a control-plane node and a worker node, built with **kubeadm** and **containerd** instead of kind.
This is how most self-managed clusters are built, and it is what the CKA exam uses.

- Your lab terminal still has `kubectl`, already connected to this cluster.
- `limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"` or `"$DOCKYARD_WORKER"` opens a shell *inside* a VM. Type `exit` to come back.
- Inside a VM, `sudo` gives you root on that VM only. Your lab terminal itself still runs with your normal permissions on your computer.
- The database keeps its data on a local volume on the worker, so it is tied to that one machine and not replicated.

Use the VM names in those two variables; do not point commands at other VMs.

```figure
lab-vms
```
