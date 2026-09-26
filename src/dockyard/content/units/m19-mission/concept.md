## Independent operations

The application, runtime, node agent, and operator client have different failure boundaries.
Use evidence to decide which boundary to investigate next, and preserve working layers while repairing failed ones.
Your earlier container and Kubernetes experience now connects to the Linux processes that implement the cluster.
This mission supplies outcomes and an existing native checkpoint; choose your own diagnostic order.

A successful HTTP request does not replace node-heartbeat evidence, and a working host client does not establish that the guest operator client is correctly configured.
The assessment checks all these boundaries against live state.

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
