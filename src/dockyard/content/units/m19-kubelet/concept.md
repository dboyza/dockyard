## When the node agent stops

The **kubelet** is the agent on each node that starts the Pods assigned to it, keeps them running, and reports back to the API server.
It runs as an ordinary Linux service managed by **systemd**.

Something surprising happens if the kubelet stops: the containers keep running.
containerd looks after them on its own, so the application can still answer requests.
What stops is *supervision*: nobody restarts failed containers, starts new Pods on that node, or reports its status.
So a working request is not proof that the node is healthy.

The API server also does not notice straight away.
Every node renews a small **Lease** object in the `kube-node-lease` namespace every few seconds.
When renewals stop, it can take up to about a minute before the node is marked `NotReady`, so for a while a stale `Ready` status can outlive the kubelet itself.

## Reading a systemd service

These commands work for any systemd service, and you will use them on the kubelet in the CKA:

```sh
systemctl status kubelet --no-pager
sudo journalctl -u kubelet -n 30 --no-pager
systemctl cat kubelet
sudo systemctl start kubelet
sudo systemctl enable kubelet
sudo systemctl daemon-reload
```

- `status` shows whether it is running (`active (running)`) and its last few log lines.
- `journalctl -u NAME` shows its full log; `-n 30` limits it to the last 30 lines.
- `systemctl cat` shows the service’s definition files, including extra “drop-in” files that change its settings, without editing anything.
- `start` runs it now; `enable` makes it start at boot. They are separate.
- After editing a service definition, run `daemon-reload` so systemd reads it, then restart the service.

A stopped service needs starting; a service with a broken configuration needs the configuration fixed.
Restarting a misconfigured service just repeats the failure, so read the journal first.
kubeadm keeps the kubelet’s settings under `/var/lib/kubelet` and its credentials under `/etc/kubernetes`.

## Worked example: the same checks on containerd

```sh
limactl shell --workdir=/tmp "$DOCKYARD_WORKER"
systemctl show containerd -p ActiveState -p SubState -p MainPID
sudo journalctl -u containerd -n 15 --no-pager
systemctl cat containerd
exit
```

`systemctl show -p` prints exactly the properties you name.
A `MainPID` links “systemd thinks it is running” to a real process.

## Checking from the API side

From your lab terminal:

```sh
kubectl get nodes
kubectl get leases -n kube-node-lease -o wide
```

A fresh lease renewal time, a `Ready` condition, and an active kubelet service together are strong evidence.
Even then, a Ready node can have broken networking, which is why Check work also runs a real job.

## Working in this lab’s machines

From this module on, Dispatch runs on two real Ubuntu virtual machines, a control-plane node and a worker node, built with **kubeadm** and **containerd** instead of kind.
This is how most self-managed clusters are built, and it is what the CKA exam uses.

- Your lab terminal still has `kubectl`, already connected to this cluster.
- `limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"` or `"$DOCKYARD_WORKER"` opens a shell *inside* a VM. Type `exit` to come back.
- Inside a VM, `sudo` gives you root on that VM only. Your lab terminal itself still runs with your normal permissions on your computer.
- The database keeps its data on a local volume on the worker, so it is tied to that one machine and not replicated.

Use the VM names in those two variables; do not point commands at other VMs.
