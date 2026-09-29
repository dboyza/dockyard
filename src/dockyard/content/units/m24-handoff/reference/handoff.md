# Operating handoff

## Symptom and evidence

Context: this lab's cluster, namespace `dispatch`.
`kubectl rollout status deployment/dispatch` timed out.
`kubectl get deployment dispatch` showed 2 desired, 1 up to date, 2 available, 3 total.
The new Pod was stuck with `ErrImageNeverPull`; its events named an image tag ending in `-missing`, which does not exist.
The two old Pods were still serving.

## Repair and verification

`kubectl rollout undo deployment/dispatch` returned to the previous revision.

To check:

- `kubectl rollout status deployment/dispatch` should report `successfully rolled out`. If it times out, look at the newest Pod's events.
- `kubectl get deployment dispatch` should show the same number for desired, up to date, and available.
- `kubectl get pods -l app=dispatch` should show only Running, Ready Pods.
- A new job should reach `done`.

## Recovery boundaries and next actions

The rollback only changed the Deployment; it would not undo database changes or replace leaked credentials.
Roll back again if a new release leaves `rollout status` waiting for more than a few minutes; ask for help if the previous revision also fails.
The API runs on one worker next to the database's volume, so losing that node would still stop Dispatch.
Find out where the `-missing` image name came from before trying the release again.
