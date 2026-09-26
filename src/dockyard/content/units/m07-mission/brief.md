# Deliver the first Kubernetes checkpoint

The starter has a Deployment scaled to zero and a Service selecting an obsolete label.
Deliver a two-replica Dispatch application in namespace `dispatch` using the supplied image.

- Keep a Deployment named `dispatch` with two available replicas and Pod label `app=dispatch`.
- Keep a Service named `dispatch` that reaches those replicas on port 8080.
- Keep manifests in the workspace so another operator can reproduce the state.
- Write `OPERATIONS.md` explaining the current context, how to inspect ownership and endpoints, and how to observe a Pod replacement.
- Demonstrate a healthy response through the Service before checking.

Equivalent declarative or imperative repair steps are accepted when the final live state and maintained source satisfy the contract.
Do not create a standalone lookalike Pod as a substitute for the required Deployment.
The runbook receives self-review; runtime criteria determine the automated result.
