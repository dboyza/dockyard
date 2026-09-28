## Each path adds a layer

A ClusterIP Service works inside the cluster, a NodePort adds a port on each node, and a LoadBalancer adds an outside address.
Each of them still depends on the same two things: selecting the right Pods, and sending traffic to the port they really listen on.

Check your understanding:
Why does a working NodePort request not prove the LoadBalancer address works?
A Service has endpoints but every request times out. Which setting would you check first?
