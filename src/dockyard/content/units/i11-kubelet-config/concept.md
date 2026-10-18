## What you’re walking into

Someone edited the kubelet's settings on the worker node.
Shortly afterwards the worker became `NotReady`.
The API still answers, and the control plane looks fine.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** the way a user would, with a new job.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

A node is `Ready` only while its kubelet keeps reporting in.
Containers that were already running can keep going for a while after the kubelet stops, so "the Pods are still there" does not mean the node is healthy.

The kubelet reads its settings from `/var/lib/kubelet/config.yaml` when it starts.
If a value in that file is invalid, the kubelet exits straight away, and systemd keeps trying to restart it.
Restarting it again will fail the same way until the file is fixed.
Settings that take a length of time expect a **duration**, written like `30s`, `5m`, or `0s`.

```sh
kubectl get nodes
kubectl describe node NODE_NAME
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" systemctl status kubelet
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo journalctl -u kubelet -n 30 --no-pager
```

Deleting the Node, resetting it with kubeadm, or rejoining it would throw away the node's identity and everything scheduled there.
The bad setting would still be waiting in the file.
