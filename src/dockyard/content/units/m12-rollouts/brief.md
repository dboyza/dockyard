## Recover from a broken release

1. Look at the rollout history and the ReplicaSets, and find which image each one uses.
2. Bring the live Deployment back to the working release, with `kubectl rollout undo` or by setting the image yourself.
3. Fix `platform.yaml` to use `${DOCKYARD_IMAGE}` again, with `maxUnavailable: 0` and `maxSurge: 1`.
4. Apply it with `python render.py platform.yaml | kubectl apply -f -`, wait for two available replicas, and check the release Dispatch reports.
5. Choose **Check work**.

Leave the failed ReplicaSet in the history, and do not delete and recreate the Deployment.
In your notes, say which command fixed the live Deployment and which edit stops the broken image coming back.
