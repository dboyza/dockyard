## Clean up the reports namespace's identities

The `reports` namespace runs everything as its `default` ServiceAccount, which holds the `edit` role and a token that never expires.

1. Inspect what the default ServiceAccount can do and which token Secrets exist.
2. Remove the broad RoleBinding and the legacy token Secret, from the cluster and from `reports.yaml`.
3. Stop the default ServiceAccount mounting tokens, and give `report-builder` its own ServiceAccount that can only read the `report-settings` ConfigMap.
4. Apply your changes, recreate the viewer, confirm the builder still logs `report_built`, and choose **Check work**.

Leave Dispatch's namespaces untouched.
In your notes, explain why deleting the legacy Secret matters even after the RoleBinding is gone.
