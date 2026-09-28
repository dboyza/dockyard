## Restore the native cluster

Get the existing environment to a state where:

- on the worker, `sudo crictl info` works with the normal `/etc/crictl.yaml`, and a running API process is under the systemd cgroup tree;
- both kubelets are active, both nodes are Ready, and their leases are fresh;
- the operator client in the control-plane VM lists both nodes with proper certificate checks and mode 600;
- all four control-plane static Pods are running, and a new job completes through the frontend and database.

Keep the current VMs, workloads, and database storage.
Write `handoff.md` listing each broken layer, the evidence for your fix, and one observation that would have proved you wrong.
