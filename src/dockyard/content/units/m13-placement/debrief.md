# Debrief: Place workloads across dedicated workers

Node labels, placement rules, and taints describe different parts of where a workload may run.
A toleration permits a placement that a taint would otherwise repel; it does not itself attract the Pod to that node.

## Explain your result

Explain how the required selector and toleration work together and why removing the node’s taint would weaken the intended boundary.

## Transfer beyond this lab

Review remaining eligible nodes and failure domains before combining hard placement rules with an availability target.
