## What you’re walking into

Someone ran a cleanup command that was broader than they meant.
It deleted the trusted frontend's Deployment in the `frontend` namespace, and the `maintenance-sentinel` ConfigMap in `default`.
The database and its data are untouched.
A snapshot of etcd taken just before the cleanup is on the control-plane node at `/var/lib/etcd/dockyard-recovery.db`.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** the way a user would, with a new job.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

Applying the original YAML again would create new objects with the same names but new UIDs.
This incident requires the original objects, with their original UIDs, so you need the snapshot.

An etcd restore is all-or-nothing: it rolls the *whole* API back to the moment of the snapshot.
Anything else changed after the snapshot would be undone too.
Here the snapshot was taken just before the cleanup, so that cost is small, but in real life weigh it before choosing a restore.

Use the procedure from the etcd lesson:
restore into a new directory with `etcdutl snapshot restore` and `--bump-revision=1000000000 --mark-compacted`, then switch the etcd manifest's data `hostPath` to it.
Never restore over the directory etcd is currently using.

Right after a restore, objects come back with the status they had when the snapshot was taken.
So `kubectl rollout status` can report success before the controllers have caught up.
Give it a minute, and check `kubectl get pods -n frontend` shows fresh, Ready Pods.
If Check work says the lab changed while it was being checked, wait a little and run it again.
