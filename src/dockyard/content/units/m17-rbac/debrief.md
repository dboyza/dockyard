# Debrief: Limit a workload API identity

The real reader token can perform its required Pod observation while Secret access and cross-namespace access are denied.
The API and worker have no automatically mounted Kubernetes token because their application work does not need API authority.

## Explain your result

Explain why a successful administrator request would not prove either workload’s effective privileges.

## Transfer beyond this lab

Use separate identities for separate responsibilities and review authorization whenever an application gains a new operational capability.
