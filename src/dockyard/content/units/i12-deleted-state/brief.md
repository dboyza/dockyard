# Incident report

An accidental API cleanup removed the trusted frontend Deployment and the maintenance sentinel.
The supplied pre-incident snapshot is at `/var/lib/etcd/dockyard-recovery.db` on the owned primary guest.
The recovery contract requires those original API identities, not recreated objects with matching names.
Recover from that snapshot while preserving the original namespace, nodes, database claim, and stored job.
Demonstrate a ready API, all control-plane processes, fresh scheduling, and a fresh job from the restored frontend.

Do not overwrite a live etcd data directory.
Use a separate restored directory and a deliberate static manifest switch.
Include a revision bump and mark the restored revision compacted for Kubernetes watch recovery.
Record the rollback implications and distinguish the API snapshot from a database backup.
Use the debrief as a self-review rubric.
