# Explain the evidence

Compare the desired replica count with the ready and available replicas you observed.
Trace one Pod's owner reference to its ReplicaSet, then to its Deployment.
Explain how the Service finds backend addresses and why Pod replacement does not require clients to learn a new address.

A passing check establishes the observed state of this practice cluster at one moment.
It does not prove that arbitrary future failures are harmless or that a two-replica Deployment is highly available across failure domains.
Both replicas can still share this lab's single node.

## Transfer

Describe the first three observations you would collect if apply succeeded but a client could not reach the application.
Return to this unit later without the reference and repeat the diagnosis from a clean starter.
