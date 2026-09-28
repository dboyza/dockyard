## Updating an application without an outage

When you change a Deployment’s Pod template, for example to a new image, Kubernetes performs a **rolling update**.
It creates a new ReplicaSet for the new version and gradually shifts Pods from the old ReplicaSet to the new one.

Two settings control the pace:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
```

- `maxSurge` is how many *extra* Pods may exist during the update.
- `maxUnavailable` is how many of the desired Pods may be unavailable during the update.

With two replicas, `maxSurge: 1` and `maxUnavailable: 0` means: start one new Pod, wait until it is ready, remove one old Pod, and repeat.
You never drop below two ready Pods, as long as there is room for the third, and as long as readiness really means ready.
The other strategy type, `Recreate`, stops all old Pods before starting new ones, which causes downtime but avoids two versions running at once.

## Changing the image

In a file, you edit the image and apply.
From the command line, which is quicker in exams:

```sh
kubectl set image deployment/dispatch api=NEW_IMAGE
```

`api` is the container’s name inside the Pod template.

## Watching and reversing a rollout

```sh
kubectl rollout status deployment/dispatch --timeout=20s
kubectl rollout history deployment/dispatch
kubectl rollout history deployment/dispatch --revision=2
kubectl get replicasets -l app=dispatch,track=stable
kubectl rollout undo deployment/dispatch
kubectl rollout undo deployment/dispatch --to-revision=1
```

- `rollout status` waits for the update to finish, or reports that it is stuck.
- `rollout history` lists revisions; `--revision=N` shows that revision’s template.
- `rollout undo` goes back to the previous revision; `--to-revision=N` goes to a specific one.
- `kubectl rollout pause` and `resume` let you stop an update partway and continue later.

To make history readable, set a note on each change:

```sh
kubectl annotate deployment/dispatch kubernetes.io/change-cause="use release 2"
```

That text appears in the CHANGE-CAUSE column of `rollout history`.

## This lab

The Deployment first ran the good image, then someone changed it to an image that does not exist.
The new Pods cannot start: look for `ErrImageNeverPull` or `ImagePullBackOff` in `describe pods`.
Worse, this Deployment’s update settings are `maxUnavailable: 2` and `maxSurge: 0`, so Kubernetes was allowed to remove both working Pods before any new one was ready.
Compare the READY column of the two ReplicaSets: the old one was scaled to zero, and the new one has no ready Pods, so Dispatch is completely down.
With `maxUnavailable: 0` and `maxSurge: 1`, the same bad image would have left the old Pods serving while the new one failed.
The failed attempt remains visible as its own ReplicaSet.

`rollout undo` fixes the live Deployment, but not your file.
`platform.yaml` still names the broken image, so the next `apply` would break it again.
Fix both.

A rollback only changes the Pod template.
It does not undo database changes a new version made, so real releases need changes that the old version can live with.
