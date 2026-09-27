## What did you allow, and what did you prevent?

The practice reader can list Pods in `dispatch`.
Requests for Secrets and for Pods in `kube-system` are refused with HTTP 403.
The API and worker still do their application work without Kubernetes API tokens.

Explain how the ServiceAccount, Role, and RoleBinding each contribute to that result.
Then predict what would break if you removed the RoleBinding entirely.
You should expect the useful Pod read to fail as well; denying everything would not meet this task’s goal.

When a real application gains a new responsibility, review its permissions again.
Give it the access needed for that responsibility rather than copying an administrator’s access.
