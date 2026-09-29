# Recovery handoff

## What was wrong, and the evidence

- API server: `crictl logs` on the latest failed container showed refused connections to etcd on port 2399; the manifest's `--etcd-servers` used 2399 while etcd listens on 2379.
- Scheduler: `/etc/kubernetes/manifests` held only three files; `kube-scheduler.yaml` had been moved to `/var/lib/dockyard/recovery/`.
- State: the `maintenance-sentinel` ConfigMap was missing, and a snapshot from before the deletion was at `/var/lib/etcd/dockyard-recovery.db`.

## What I changed, in order

1. Corrected `--etcd-servers` to `https://127.0.0.1:2379`, keeping every certificate flag.
2. Moved the scheduler manifest back into `/etc/kubernetes/manifests`.
3. Checked the snapshot with `etcdutl snapshot status`, restored it into `/var/lib/etcd/dockyard-restored` with `--bump-revision=1000000000 --mark-compacted`, and pointed the etcd manifest's data `hostPath` at that directory. The old manifest is saved in `/var/lib/dockyard`.

## How I checked the recovery

- `kubectl get --raw=/readyz` returned ok.
- The sentinel's UID matched the original.
- A new test Pod was scheduled onto a node, and a new Dispatch job completed.
- The database row written before the incident was still present.

## What the etcd snapshot covers, and what it does not

The snapshot holds Kubernetes objects, including Secrets, so it must be protected like a credential.
It does not hold PostgreSQL's rows, which live on the worker's volume and need their own backups.
The restore also rolled back any other API change made after the snapshot.

## What a production plan would add

More than one control-plane node, so one bad manifest does not stop the API.
Scheduled snapshots stored away from the cluster, and regular restore practice.
Separate, tested database backups.
