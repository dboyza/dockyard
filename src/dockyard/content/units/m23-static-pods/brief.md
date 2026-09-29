## Bring back the kubelet and the scheduler

- On the control-plane node, the kubelet is stopped and the scheduler's manifest is missing from `/etc/kubernetes/manifests`.
- Put the scheduler's manifest back and start the kubelet.
- Show that a brand-new Pod gets a node, for example with `python wait-control-plane.py`.
- Keep the cluster, its nodes, and the database's data; do not rebuild anything.

In your notes, explain why Pods that were already running did not prove the cluster was healthy.
