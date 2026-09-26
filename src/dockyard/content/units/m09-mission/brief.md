# Deliver learning and preview environments

Repair `dispatch` and the supplied `preview` manifests using the same application image.

- `dispatch` must report environment `learning`; `preview` must report `preview`.
- Both APIs must read the required banner through a ConfigMap volume and authenticate through their own mounted database Secret.
- Each namespace must contain its own database, queue, worker Deployment, and Service destinations.
- Both environments must process a newly submitted job with the correct result.
- The dispatch inventory identity may list local Pods, but may not list Secrets or kube-system Pods.
- Business API Pods must have automatic ServiceAccount token mounting disabled.
- Record configuration refresh rules and the remaining ephemeral-storage limitation in `ENVIRONMENTS.md`.

The preview credential uses the lab practice password with a `-preview` suffix and is already expressed as a Secret template.
Do not print or copy its resolved value into your notes.
The checker observes live behavior; your explanation is retained for self-review.
