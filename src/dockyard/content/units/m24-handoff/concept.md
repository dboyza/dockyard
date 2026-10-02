## Still answering is not the same as finished

The Dispatch API uses a rolling update that never takes an old Pod away before a new one is ready (`maxUnavailable: 0`, `maxSurge: 1`).
That is good for users: if the new version cannot start, the old Pods keep serving.
It also means a failed release can go unnoticed, because health checks still pass.

In this lab, someone changed the API's image to one that does not exist.
The old Pods are still answering, and one new Pod is stuck.

A Deployment reports four numbers, and together they tell you whether a rollout has finished:

| Column | Meaning |
| --- | --- |
| desired (`spec.replicas`) | how many copies you asked for |
| `UP-TO-DATE` | how many run the newest template |
| `AVAILABLE` | how many are ready to serve |
| total (`status.replicas`) | how many exist, old and new together |

A rollout is done only when all four agree.

```figure
rollout-columns
```

## Worked example: read the rollout

```sh
kubectl rollout status deployment/dispatch --timeout=20s
kubectl get deployment dispatch -o wide
kubectl get pods -l app=dispatch
kubectl rollout history deployment/dispatch
```

`rollout status` times out instead of finishing.
`get deployment` shows fewer up-to-date copies than desired, and `-o wide` shows the image it is trying to use.
One Pod is stuck in `ErrImageNeverPull`; `kubectl describe pod POD_NAME` shows the exact image name in its events.
`ErrImageNeverPull` means the Pod's `imagePullPolicy` is `Never`, so the kubelet may only use images already on the node, and this one is not there.
With a normal pull policy the same mistake shows as `ErrImagePull` and then `ImagePullBackOff`.
`rollout history` lists earlier revisions you can go back to.

## Fix it

Either go back to the previous revision:

```sh
kubectl rollout undo deployment/dispatch
```

or set a valid image with `kubectl set image deployment/dispatch api=IMAGE`; in this lab `$DOCKYARD_IMAGE` holds the name of the working Dispatch image.
In this lab the previous revision is known to work, so `undo` is the simplest choice.
Then wait for `kubectl rollout status deployment/dispatch` to finish, check the stuck Pod has gone, and submit a new job.

A rollback only changes the Deployment.
It does not undo database changes a new version made, bring back deleted data, or replace a leaked password.
Say so in your handoff, so nobody assumes more was restored than really was.

## Write a handoff someone else can use

A **handoff** is a note for the next person on call, who did not see your terminal.
Write `handoff.md` so they could check the system and spot the same problem again on their own:

- the context and namespace you worked in;
- the symptom, and the evidence that showed its cause;
- what you changed;
- the commands that check the result, what each should show, and what it would mean if it showed something else;
- when to roll back, and when to ask for help;
- what this setup still cannot survive, such as losing its only worker.

Never paste kubeconfigs, tokens, passwords, or private keys into a handoff.
Check work tests the Deployment and a real job; your handoff is for you to compare with the reference.
