## Replace an impossible request

Both API replicas request and limit 99 CPUs, so neither can be scheduled.

1. Read the Pods’ scheduling events and compare the request with the node’s allocatable CPU.
2. In `platform.yaml`, give the API requests of `50m` CPU and `64Mi` memory, and limits of `300m` CPU and `192Mi` memory. Apply it and wait for two available replicas.
3. Add the LimitRange and ResourceQuota from Understand to `capacity.yaml`, keeping the disruption budget already in it, and apply it.
4. Look at `kubectl describe quota dispatch-budget` and each Pod’s QoS class.
5. Choose **Check work**.

In your notes, explain the difference between a Pod that cannot be scheduled because of its request, and a running container killed for going over its memory limit.
