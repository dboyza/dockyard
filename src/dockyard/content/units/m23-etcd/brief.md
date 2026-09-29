## Back up etcd, lose an object, and restore it

1. Inside the control-plane VM, save a snapshot to `/var/lib/etcd/dockyard-recovery.db` and check it with `etcdutl snapshot status`.
2. In the lab terminal, run `python -m dockyard.fixtures.recovery stage-loss` to delete the original `maintenance-sentinel` ConfigMap.
3. Restore the snapshot into a new directory, `/var/lib/etcd/dockyard-restored`, with `--bump-revision=1000000000 --mark-compacted`.
4. Point the etcd manifest's data `hostPath` at the restored directory, keeping a copy of the old manifest outside `/etc/kubernetes/manifests`.
5. Run `python wait-control-plane.py`, then check the sentinel is back with its original UID.

Do not recreate the ConfigMap by hand, and keep the snapshot and certificates inside the VM.
