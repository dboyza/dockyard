## One version, one node, one step at a time

You upgraded kubeadm, then the control plane, then each node’s kubelet, draining each node first, and the same cluster came out on 1.37.1 with its data intact.

Check your understanding:
Why does the worker run `kubeadm upgrade node` rather than `upgrade apply`?
What would you back up before doing this on a production cluster?
