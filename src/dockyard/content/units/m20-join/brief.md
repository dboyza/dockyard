## Join the worker and bring up networking

1. Look at the nodes and kube-system Pods before joining.
2. Join the worker with the CA-pinned configuration from Understand.
3. Generate and read the network manifest, then apply it and wait for the nodes, Calico, and CoreDNS.
4. Run `sh bootstrap.sh` to deploy Dispatch.
5. Choose **Check work**.

Both nodes must be Ready, Calico must be ready on both, CoreDNS available, and a new job from the frontend must complete.
In your notes, say which observation shows each of: the worker registered, the network is ready, DNS works, and real traffic flows.
