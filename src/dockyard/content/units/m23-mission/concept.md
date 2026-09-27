## Independent recovery brief

The primary API is unavailable, the scheduler manifest is displaced, and an original Kubernetes sentinel object has been deleted.
A verified pre-loss snapshot exists inside the running etcd container at `/var/lib/etcd/dockyard-recovery.db`.
The workload database remains on the worker's existing volume.
Recover the current cluster instead of replacing it.

Use the diagnostic methods and restore procedure from the three preceding lessons.
Choose a recovery order that respects dependencies and avoids treating the unavailable API as your only diagnostic interface.
The snapshot must recover the original object UID, not merely its name or contents.
Use the taught revision bump and compaction strategy, then establish that new writes and scheduler assignments work.

## Handoff requirements

In `handoff.md`, identify the observed failure at each layer, the evidence that supported your repair, and the recovery sequence.
Separate the etcd snapshot's Kubernetes-state boundary from the preserved PostgreSQL volume.
Record how you proved original identity, new scheduling, and a complete new job.
Explain the single-control-plane interruption, the local-volume dependency, and what a production recovery plan would additionally protect.
This narrative is assessed through an explicit self-review rubric; runtime checks independently verify the observable technical outcomes.
