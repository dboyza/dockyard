## What changed

The partner's code now runs inside gVisor, its credentials are encrypted in etcd and its backups, and its traffic between nodes travels inside WireGuard.
Each layer covers a different path: the node's kernel, the cluster's storage, and the network between machines.

Check your understanding.
Which layer would still protect the partner token if an attacker stole an etcd backup?
Which layer would protect the node if the plugin code were malicious?
What does none of these layers protect against?
