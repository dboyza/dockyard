# Remove an unnecessary API permission

The inventory Role can read Secrets as well as Pods.
Inspect identity.yaml, its RoleBinding, and the process that actually uses the account.
Restrict the Role to its required Pod reads and apply the repaired identity file with the supplied renderer.
Keep the API and worker token-free while leaving inventory's projected token available for its actual purpose.
Verify successful Pod reads, forbidden Secret reads, forbidden access to kube-system Pods, and a working job-processing path.
