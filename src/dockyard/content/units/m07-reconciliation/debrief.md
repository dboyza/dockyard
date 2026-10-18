## Why did the replacement appear?

Your Deployment still asked for two copies after you deleted one Pod.
The ReplicaSet created another Pod to bring the number back to two.
The new Pod has its own name and UID; the old Pod did not restart.

Without looking back, explain what you expect if you delete the Deployment instead.
Then explain why two Pods on this one node would both be affected if the node stopped.

A passing check confirms two working copies owned by this Deployment, a working Service, and that the ReplicaSet replaced a Pod you removed.
It cannot tell whether you watched the replacement appear.
If you only deleted the Pod and checked, delete another one and watch it with kubectl get pods --watch before moving on.
