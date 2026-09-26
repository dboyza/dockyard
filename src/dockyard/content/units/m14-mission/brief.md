# Make both environments reproducible

Repair the development overlay to two API replicas and environment development.
Render and apply it, then restart the API to refresh its ConfigMap environment.
Recover the staging Helm release using its healthy revision and fix the practice values to two replicas and environment staging.
Restore the WorkerPool controller to one replica while keeping the ordinary development worker Deployment at zero.
Wait for the pool's two managed workers and run the drift rehearsal.

Inspect the actual application environment in both namespaces and prove job processing by the operator-owned workers.
Keep staging's release history and database claim.
Do not apply Kustomize's staging example over Helm-owned resources.
Write a handoff note naming each source of truth, the recovered Helm revision, and the worker ownership chain.
