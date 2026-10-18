## Compare your recovery

There were three faults.
The API server's `--etcd-servers` pointed at the wrong port.
The scheduler's manifest had been moved out of `/etc/kubernetes/manifests`.
The sentinel had been deleted after the snapshot.
The node's own tools found the first two: the API server's container log showed refused connections to etcd, and the manifests directory had only three files.
The restore brought back the original sentinel, and the revision bump made controllers re-read the restored state.
A fresh Pod getting a node, and a new job completing, showed the cluster could do new work, not just keep old work running.

Your order may differ.
Restoring etcd works while the API server is down, because you run the etcd tools through `crictl` on the node.
What matters is that each fix was based on evidence and checked afterwards.

## Check your understanding

- For each fault, which layer was it in, and which tool showed it?
- Why did the database row survive, and what would you have needed if it had not?
- What in your handoff would help someone who faces this at 3 a.m.?

## Beyond this lab

With one control-plane node, any of these faults stops the whole API.
Production clusters run three or more control-plane nodes, store etcd snapshots away from the cluster, and practise restores regularly.
