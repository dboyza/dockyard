## Recover the control plane

- Bring back the API server and make sure new Pods are scheduled again.
- Restore the deleted `maintenance-sentinel` from the snapshot at `/var/lib/etcd/dockyard-recovery.db`, with its original UID.
- Keep the original cluster, nodes, and database data.
- Show a new Pod getting a node and a new Dispatch job completing.
- Write your recovery notes in `handoff.md`.
