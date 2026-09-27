# Debrief: Join a worker and establish cross-node networking

Joining the worker establishes membership, but CNI agents, DNS, and actual cross-node traffic still need independent verification.
The fresh frontend job crosses the network and reaches persistent data, closing gaps that a pair of Ready nodes would leave open.

## Explain your result

Trace the bootstrap credential’s role in joining and distinguish it from the certificates used by the node afterward.

## Transfer beyond this lab

Protect join material and verify node addressing and network ranges before extending a production cluster.
