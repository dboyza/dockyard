## Let the inventory Pod list Pods, and nothing more

The `inventory` Deployment runs as the `dispatch-reader` ServiceAccount, but the RoleBinding grants the Pod-reading Role to a different account.

1. Find which ServiceAccount the inventory Pod uses and which one the RoleBinding names.
2. Fix the RoleBinding in `identity.yaml` so `dispatch-reader` gets the existing `dispatch-pod-reader` Role.
3. Apply it and test with `kubectl auth can-i` and with the request from the Pod itself.
4. Choose **Check work**.

Do not widen access: keep the narrow Role, and do not bind `cluster-admin` or a wildcard role.
Keep token mounting turned off for the `dispatch-app` account used by the API and workers.
