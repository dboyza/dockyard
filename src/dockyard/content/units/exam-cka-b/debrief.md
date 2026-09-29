## Reviewing your attempt

Open each task in the results to see what Dockyard checked and what it found.
A task can earn part of its marks when some of its checks pass.

Common gaps in this exam:

- a newer kubectl does not mean the cluster was upgraded; check `kubectl get --raw=/version` and each node's kubelet version;
- a renewed certificate file does nothing until the API server restarts and serves it;
- fixing a NetworkPolicy by allowing everything loses the marks for the rules that should still deny traffic;
- a PodDisruptionBudget must allow exactly the disruptions asked for; check `ALLOWED DISRUPTIONS`.

For each task you missed, work through the lesson it links to, then try a fresh attempt without help.
