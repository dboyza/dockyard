## Run learning and preview environments side by side

Fix the `dispatch` manifests and the supplied `preview.yaml` so both environments run from the same image:

- `dispatch` reports environment `learning`, and `preview` reports `preview`.
- Both APIs read the required banner from a ConfigMap volume and log in to their own database using their own mounted Secret.
- Each namespace has its own database, queue, workers, and Services.
- Both environments complete a new job with the correct result.
- The `dispatch` inventory identity can list Pods in `dispatch`, but not Secrets, and not Pods in `kube-system`.
- The API Pods do not have a ServiceAccount token mounted.

Write `ENVIRONMENTS.md` explaining when configuration changes reach running Pods and what the ephemeral database still means for each environment.

The preview password is the lab’s practice password with `-preview` on the end, already set up in a Secret template.
Do not print it or copy it into your notes.
