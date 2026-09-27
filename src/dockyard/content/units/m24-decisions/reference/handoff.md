# Operating handoff

I compared actual endpoint selection, workload revisions, and dependent worker capacity before changing the environment.
I used scoped configuration corrections and observed the resulting rollout and a complete new Dispatch transaction.
The private cluster and original database row were preserved.
Use kubectl get deployments, kubectl get pdb, and a fresh application job to repeat the workload verification.
Inspect inventory permissions with its actual identity, not the administrator session.
A Deployment rollback cannot restore PostgreSQL data or revoke leaked credentials.
The single application worker and local database volume remain failure boundaries even when the API voting majority survives.
