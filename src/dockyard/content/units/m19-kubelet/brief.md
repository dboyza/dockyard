## Restore the worker’s kubelet

The kubelet on the worker is not supervising the node, though existing containers still run.

1. Enter the worker and run `systemctl status kubelet --no-pager`, `sudo journalctl -u kubelet -n 30 --no-pager`, and `systemctl cat kubelet`.
2. Decide whether the service just needs starting, or has a configuration problem to fix first, and repair it.
3. Exit, then check both nodes are `Ready` and compare their lease renewal times with `kubectl get leases -n kube-node-lease -o wide`.
4. Choose **Check work**.

Do not replace the VM or rebuild Dispatch; a new job must complete through the existing application.
In your notes, explain how a container can keep running while its node has lost supervision.
