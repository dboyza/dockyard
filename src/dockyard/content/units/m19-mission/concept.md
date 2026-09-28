## Recover the whole chain

This mission combines the three lessons: several layers of the native cluster are broken at once.
The application, the container runtime tools, the kubelet, and the separate operator client can each fail on their own, and each can look fine while its neighbour is broken.

There are no step-by-step commands.
Decide your own order, collect evidence before each change, and leave working layers alone.

Remember the traps from the lessons:

- a successful HTTP request does not show the kubelet is supervising the node;
- a working `kubectl` in your lab terminal says nothing about the operator client inside the VM;
- a Ready status can be stale; a fresh lease renewal is stronger evidence.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Working in this lab’s machines

From this module on, Dispatch runs on two real Ubuntu virtual machines, a control-plane node and a worker node, built with **kubeadm** and **containerd** instead of kind.
This is how most self-managed clusters are built, and it is what the CKA exam uses.

- Your lab terminal still has `kubectl`, already connected to this cluster.
- `limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"` or `"$DOCKYARD_WORKER"` opens a shell *inside* a VM. Type `exit` to come back.
- Inside a VM, `sudo` gives you root on that VM only. Your lab terminal itself still runs with your normal permissions on your computer.
- The database keeps its data on a local volume on the worker, so it is tied to that one machine and not replicated.

Use the VM names in those two variables; do not point commands at other VMs.
