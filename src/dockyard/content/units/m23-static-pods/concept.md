## Running containers can outlive their reconciler

Kubelet reconciles Pod specifications with the container runtime.
Stopping kubelet does not necessarily stop every existing container immediately.
A working API or an old running workload therefore does not establish that the host can reconcile changes.
The scheduler is a separate process that assigns unscheduled Pods to nodes.
Both mechanisms must work to create useful new workloads.

This fixture moves the scheduler's manifest outside the watched directory, waits for its container to stop, and then stops the primary kubelet.
The original manifest remains at `/var/lib/dockyard/recovery/kube-scheduler.yaml`.
Recover each boundary deliberately.
Starting kubelet alone will not reconstruct a manifest that is absent from disk.
Restoring the file alone cannot make a stopped kubelet process it.

## Worked example: follow ownership

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" systemctl status kubelet
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo journalctl -u kubelet -n 40 --no-pager
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo ls /etc/kubernetes/manifests
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl ps -a
```

Match the service state, manifest inventory, and runtime container inventory.
The API's mirror Pod represents a kubelet-managed static Pod; deleting that mirror object is not a durable repair of the host manifest.
Restore the known scheduler file to `/etc/kubernetes/manifests/kube-scheduler.yaml` and start kubelet through systemd.
Keep backups outside the watched directory and preserve the supplied certificates and other components.

## Ask the scheduler to do something new

An already assigned Pod can keep running when the scheduler is absent.
Create a fresh Pod without a `nodeName`, then inspect its PodScheduled condition and assigned node.
The assessment does this with a unique disposable Pod copied from the trusted frontend's scheduling specification, then removes only that probe.
It also checks actual running control-plane processes, original cluster/data identities, and a new application transaction.
A Ready status by itself is only one observation in that chain.

The supplied `python wait-control-plane.py` helper retries a read and a write against the recovering API, then observes a fresh scheduler assignment before deleting its disposable Pod.
Its source is available in the workspace so you can inspect the exact observations.
The scheduler may need longer to recover its watches and leadership than the API needs to answer a readiness request.
You may perform equivalent explicit checks yourself.
