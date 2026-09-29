## What you did

You backed up etcd, lost an object, and brought back the original, with its original UID, from the snapshot.
You restored into a new directory and switched the static Pod's `hostPath`, so the old data stayed untouched in case you needed to go back.
The revision bump and compaction made controllers re-read the cluster instead of trusting what they had seen before.
The database row survived because it was never in etcd: it lives on the application's volume.

## Check your understanding

- Why would recreating `maintenance-sentinel` from a YAML file not count as a restore?
- What could go wrong for controllers if etcd's revision counter went backwards?
- Which other objects in the cluster would the restore also roll back, if they had changed after the snapshot?

## Beyond this lab

Real clusters take etcd snapshots on a schedule, store them off the node, and practise restoring them.
Protect snapshots like credentials, because they contain every Secret.
Back up application data separately; an etcd restore never brings back a deleted database row.
