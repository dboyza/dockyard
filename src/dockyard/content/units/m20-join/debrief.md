## A real two-node cluster

The worker joined only after proving it had a valid token and checking it was talking to the right cluster.
Calico then connected the nodes, and a real job crossing both machines proved it.

Check your understanding:
What does the bootstrap token do, and what does the CA hash do?
Why were both nodes NotReady until Calico was installed?
