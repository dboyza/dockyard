## Deliver Dispatch on Kubernetes

The starter Deployment asks for zero copies, and the Service selects an old label.
Deliver a working two-copy Dispatch in the `dispatch` namespace using the supplied image.

- Keep the Deployment named `dispatch`, with two available copies and the Pod label `app=dispatch`.
- Keep the Service named `dispatch`, reaching those copies on port 8080.
- Keep your fixed manifests in the workspace.
- Write `OPERATIONS.md` explaining how to check the current context, how to see which Pods the Service reaches, and how to watch a Pod being replaced.
- Show a successful request through the Service before checking.

Any approach that leaves the live cluster and your files in that state is accepted.
Do not create a standalone Pod instead of fixing the Deployment.
