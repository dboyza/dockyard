# Restore the desired service

Dispatch's supplied image is already built and loaded into this cluster.
The starter Deployment requests zero replicas, so an accepted API object exists without any running application.

1. Inspect the Deployment, ReplicaSet, and Pods before editing anything.
2. Change `deployment.yaml` to request two replicas, leaving the supplied image and selector intact.
3. Run `sh run.sh`, then `kubectl rollout status deployment/dispatch --timeout=90s`.
4. Delete one practice Pod and observe reconciliation replace it.
5. Check the lab after both replicas are available again.

The check requires two available replicas owned by the Deployment, a genuine Dispatch response from each replica, and a working Service request.
The deletion observation is for your explanation and notes; the checker does not claim to prove you performed it.
