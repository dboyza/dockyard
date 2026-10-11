## Turn on audit logging and find a Secret reader

Something reads the Dispatch database password every 20 seconds, and nobody knows what.

1. Replace the draft `audit-policy.yaml` with a policy that records Secret access at `Metadata` only, workload changes in full, and skips noise.
2. Turn on auditing in the API server with that policy, a log path, and log rotation.
3. Use the audit log to find the identity that reads `dispatch-database`, and write its full username into `finding.txt`.
4. Choose **Check work**.

Never let Secret contents reach the audit log.
In your notes, explain why the order of the policy's rules matters.
