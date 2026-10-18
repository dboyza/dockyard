## Lock Dispatch down without breaking it

Fix the authored files so that:

- the reader identity can list Pods in `dispatch` but cannot read Secrets or reach other namespaces;
- only trusted frontend Pods in the `frontend` namespace reach the API, DNS works over UDP and TCP, and the default-deny policy stays;
- the namespace enforces Restricted, and the API runs with no privilege escalation, no capabilities, and a read-only root filesystem.

Apply the changes and roll out the API.
Then show the allowed and blocked paths across both nodes, a compliant and a rejected Pod at admission, and the running process’s real restrictions.
A submitted job must still complete through the API, queue, worker, and database.

Write `SECURITY-NOTES.md`: for each control, the thing it protects, one allowed and one blocked observation, and what this local exercise does not prove about production security.
