## Three APIs, three different questions

`kubectl` talks to the Kubernetes API server about desired and observed objects.
On each node, kubelet asks the container runtime to create and maintain Pod sandboxes and containers through the Container Runtime Interface, or CRI.
`crictl` is a diagnostic client of that same interface; `ctr` is containerd's lower-level administrative client.
A successful `ctr` command does not prove that the CRI plugin is ready, and a broken `crictl` configuration does not itself stop existing containers.
Here the CRI endpoint is the Unix socket `/run/containerd/containerd.sock` inside the guest.
The Docker daemon on your Mac is a separate runtime used to build and cache images.

## What cgroups establish

Linux cgroups account for and limit process resources.
This checkpoint uses cgroup v2 with the systemd driver, so containerd and kubelet cooperate with systemd's hierarchy.
A configuration value is a statement of intent; a live process under a `kubepods.slice` path is evidence that a Kubernetes workload actually uses that hierarchy.
Kubernetes 1.35 can discover the driver from a compatible runtime, including the containerd 2 runtime pinned here.
Do not switch drivers on a live node merely to make a diagnostic command succeed.

## Worked example: inspect a different component

Enter the control-plane guest and inspect the API server's runtime container:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"
sudo crictl info
sudo crictl ps --name kube-apiserver
sudo crictl inspect CONTAINER_ID
```

Replace `CONTAINER_ID` with the ID you actually observed, and find `info.pid` in the inspection output.
Then inspect `/proc/PID/cgroup` using that actual numeric PID.
The container ID, process ID, and Kubernetes Pod name are different identifiers for related objects.
`crictl` needs guest-root access to the containerd socket in this fixture.
Exit the guest before running host-side Dockyard commands.

## Diagnose the layer before changing it

An endpoint connection error may mean the client is aimed at a nonexistent socket, the daemon is stopped, or the runtime plugin is unhealthy.
Compare the socket path in `/etc/crictl.yaml`, `systemctl is-active containerd`, and kubelet's observed node health.
The first observation that contradicts your hypothesis should change your next action.

## The native checkpoint

Dispatch now runs on two real Ubuntu guests, with containerd and kubeadm rather than kind nodes.
The host terminal keeps its private Kubernetes client; `limactl` opens a separate Linux guest session.
The guest's root account is confined to that app-owned VM, but the external macOS shell still has your normal user privileges.
No host directories are mounted into either guest.
The database uses a retained local PersistentVolume on the worker, which deliberately has node affinity and is not replicated storage.
The hardened API, queue, worker, and frontend retain the application and access boundaries from the previous phase.

Use `exit` to return from a guest shell to the Dockyard workspace.
The variables `DOCKYARD_CONTROL_PLANE` and `DOCKYARD_WORKER` name this attempt's guests; do not substitute unrelated VM names.
The lab's resource panel shows the recorded guests and their state.
