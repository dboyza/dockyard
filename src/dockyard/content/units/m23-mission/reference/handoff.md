# Recovery handoff

The API dependency endpoint was incorrect, and the scheduler manifest was outside its watched directory.
I repaired the endpoint, restored the scheduler manifest, and restored the pre-loss etcd snapshot into a separate directory with a revision bump and watch compaction.
Original object identities and the pre-maintenance PostgreSQL row survived.
A new scheduler assignment and a fresh Dispatch job demonstrated useful recovery.
The etcd snapshot contained Kubernetes state, while PostgreSQL depended on its separate worker volume.
This single-control-plane exercise includes an API interruption and does not demonstrate replicated application storage.
