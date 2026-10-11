## Find and contain the compromised workload

Requirements:

- **Identify**: write the compromised workload into `finding.txt` as `NAMESPACE/NAME`.
- **Revoke**: its identity can no longer read or list Secrets in `dispatch`.
- **Isolate**: its Pod can no longer reach the Kubernetes API, the metadata address `169.254.169.254`, or DNS.
- **Preserve**: the original Pod keeps running, for examination; do not delete or restart it.

Falco is installed on the worker, ready to be started.
Dispatch must keep processing jobs, and the original namespace, nodes, marker object, and stored data must remain.

Write `incident-report.md` covering how you detected it, what it could do and why, how you contained it, and what should happen next.
Then compare it with `report-rubric.md`.
