## Make both environments reproducible

- **Development**: fix the overlay to two API replicas and environment `development`, apply it, and restart the API.
- **Staging**: roll the Helm release back to its healthy revision, and fix `values-practice.yaml` to two replicas and environment `staging`.
- **Workers**: start the WorkerPool controller with one replica, keep the ordinary development `worker` Deployment at zero, wait for the pool’s two workers, and run `python operator-proof.py`.

Check both namespaces’ `/config` responses and that the operator’s workers process a job.
Keep staging’s release history and database storage, and do not apply the Kustomize staging overlay over Helm’s objects.

Write a handoff note naming each environment’s source of truth, the Helm revision you recovered, and the chain from WorkerPool to worker Pods.
