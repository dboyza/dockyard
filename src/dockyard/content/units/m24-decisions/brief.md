## Bring the API back within the team's limits

- Run 2 to 4 API copies.
  Total requests must be at most 1 CPU and 512 MiB, and total memory limits at most 1 GiB.
  Each limit must be at least its request.
- Create a PodDisruptionBudget named `dispatch-operations` for the Pods labeled `app: dispatch` and `track: stable` that keeps at least one available.
- Put `dispatch-reader` back to reading Pods only: no Secrets, no changing Deployments, no creating RoleBindings.
- Keep the cluster and database as they are, and show a new job still completes.

In `handoff.md`, show your sums, and say what two API copies do and do not protect against.
