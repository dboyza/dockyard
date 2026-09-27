# Keep two copies of Dispatch running

Dispatch's supplied image is already built and loaded into this cluster.
The Deployment currently asks for zero copies.
Your goal is to run two copies and see Kubernetes replace one after you remove it.

1. Inspect the Deployment, ReplicaSet, and Pods before editing anything.
2. Change `deployment.yaml` to request two replicas, leaving the supplied image and selector intact.
3. Run `sh run.sh`, then `kubectl rollout status deployment/dispatch --timeout=90s`.
4. Write down one Pod’s name and UID, delete that Pod, then watch for its replacement.
   The Understand tab shows how to select a Pod and stop the watch.
5. Check the lab after both replicas are available again.

The check requires two available replicas owned by the Deployment, a genuine Dispatch response from each replica, and a working Service request.
Before checking, explain why the replacement appeared even though you did not run `kubectl apply` again.
Record the old and new Pod names in your notes.
The checker tests the two running copies and their responses; it does not record the deletion or grade your explanation.
