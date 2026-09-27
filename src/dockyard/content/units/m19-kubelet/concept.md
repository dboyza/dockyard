## A running process is not a supervised node

Kubelet watches assigned Pod specifications and reconciles their runtime state on one node.
Containerd and its shims can keep existing containers running while kubelet is stopped.
That makes an HTTP success a useful application observation but insufficient evidence of node health.
The API does not instantly mark a node NotReady when its last heartbeat stops; its controllers need time to detect the missing updates.
A cached Ready condition can therefore outlive the process that produced it.

## Follow the supervision chain

systemd starts kubelet from its service unit and drop-in configuration.
Kubeadm supplies configuration under `/var/lib/kubelet` and credentials under `/etc/kubernetes`.
`systemctl status` describes the service and recent messages, while `journalctl -u kubelet` provides its journal history.
`systemctl cat kubelet` reveals the effective unit files and drop-ins without changing them.
Starting a stopped service and fixing an invalid service configuration are different repairs.
Repeated restarts of a misconfigured service only repeat the failure.

## Worked example: inspect containerd without changing it

```sh
limactl shell --workdir=/tmp "$DOCKYARD_WORKER"
systemctl show containerd -p ActiveState -p SubState -p MainPID
sudo journalctl -u containerd -n 15 --no-pager
systemctl cat containerd
```

An active state establishes that systemd considers the service running; its PID links that claim to an actual process.
The journal helps explain failed starts, but the absence of a recent error line does not establish application correctness.
Apply this same observation pattern to kubelet for the task.

## Verify at the API boundary

Each node renews a Lease in `kube-node-lease`.
A fresh `renewTime`, a Ready condition, and an active kubelet service together provide stronger evidence than any one of them alone.
Inspect leases with `kubectl get leases -n kube-node-lease -o wide` from the host's private client.
A Ready node can still have broken CNI or DNS, so the application check additionally exercises the actual frontend, API, queue, worker, and database path.

## The native checkpoint

Dispatch now runs on two real Ubuntu guests, with containerd and kubeadm rather than kind nodes.
The host terminal keeps its private Kubernetes client; `limactl` opens a separate Linux guest session.
The guest's root account is confined to that app-owned VM, but the external host shell still has your normal user privileges.
No host directories are mounted into either guest.
The database uses a retained local PersistentVolume on the worker, which deliberately has node affinity and is not replicated storage.
The hardened API, queue, worker, and frontend retain the application and access boundaries from the previous phase.

Use `exit` to return from a guest shell to the Dockyard workspace.
The variables `DOCKYARD_CONTROL_PLANE` and `DOCKYARD_WORKER` name this attempt's guests; do not substitute unrelated VM names.
The lab's resource panel shows the recorded guests and their state.
