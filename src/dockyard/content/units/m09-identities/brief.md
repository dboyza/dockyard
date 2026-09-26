# Repair the binding without broadening access

The inventory Deployment uses `dispatch-reader`, but the RoleBinding mistakenly names another ServiceAccount.

Repair the binding so the inventory client can list Pods in `dispatch`.
Preserve its narrow Role and do not attach cluster-admin or a broad wildcard role.
Keep `dispatch-app` token mounting disabled for the API and workers.
Verify the expected allowed request and both denied requests, then check the lab.
A green administrator `kubectl get pods` does not prove that the application's identity has the required permission.
