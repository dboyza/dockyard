# Access review report

## Findings and fixes

- Anonymous callers could read everything in `dispatch` through the RoleBinding `legacy-dashboard` to `system:anonymous`. Deleted it, and limited anonymous access to `/livez`, `/readyz`, and `/healthz` with an authentication configuration.
- The Secret `deployer-token` in `ci` held a token for the CI deployer that never expires. Deleted it; the deployer's Pods use bound tokens.
- The `auditors` group held `admin` in every namespace. Replaced it with RoleBindings to `view` in `dispatch` and `frontend`.

## Evidence

- An unauthenticated request for Pods in `dispatch` and for `/version` returns 401, and `/readyz` still returns 200.
- No Secret of type `kubernetes.io/service-account-token` remains outside `kube-system`.
- `kubectl auth can-i --as=sam --as-group=auditors` allows listing Pods in both namespaces and refuses Secrets, changes, and other namespaces.

## Remaining risks

- `kubeadm join` discovery needs anonymous access to `cluster-info`; adding nodes now needs a different discovery method.
- Anyone who copied `deployer-token` before today lost access only now; check the API server's audit log once auditing is on.
