# Recover API history after an accidental deletion

Reapplying a manifest can recreate an object with the same name and desired fields, but it creates a new identity.
A point-in-time etcd restore recovers the API state represented by its snapshot, including object UIDs.
It also rolls back unrelated API changes after that snapshot.
For a separate example, restoring yesterday's backup to recover one deleted Role could discard today's authorized configuration changes.
Make that tradeoff explicit before choosing a cluster-wide restore.

This isolated incident deliberately requires the original identities and supplies a verified pre-deletion snapshot.
Use an offline destination directory, correct member identity, revision bump, and compaction so Kubernetes watchers do not silently retain a view newer than the restored data.
The database files are separate from etcd and are preserved independently.
A healthy etcd process alone does not establish that controller watches, scheduling, and the application have recovered.
