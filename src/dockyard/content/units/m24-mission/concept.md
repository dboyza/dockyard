## Independent operating contract

Dispatch runs on a three-control-plane, one-worker cluster.
The primary API server and etcd member are deliberately stopped, but the other two voters retain quorum.
The private endpoint routes incorrectly, the application route selects the wrong track, the worker process is scaled away, and inventory access is overbroad.
Recover useful operation while leaving the primary outage in place.
Do not remove its etcd member or rebuild the cluster to make the symptoms disappear.

Meet the capacity and disruption constraints taught in this chapter: two to four available API replicas, aggregate requests within one CPU and 512 MiB, aggregate memory limits within 1 GiB, and a stable-API disruption budget protecting one available replica.
Restore the inventory identity's allowed Pod reads and denied privileged operations.
Keep original namespace, node, and sentinel identities and the pre-existing PostgreSQL row.

## Deliver a verifiable handoff

Use the terminal to inspect, plan, repair, and verify each boundary.
The assessment independently observes the stopped primary components, both surviving voting endpoints, a fresh API write through the repaired endpoint, workload capacity, real token authorization, and a complete new job.
Repairing only the load balancer is insufficient.
Restarting the primary is also insufficient: this exercise asks you to demonstrate operation through its outage.

Write `handoff.md` describing failure symptoms, supporting observations, your repair order, and commands that reproduce the final verification.
Explain the remaining single application worker, local database volume, and API load-balancer placement as explicit availability limitations.
Distinguish surviving an API member outage from full end-to-end infrastructure high availability.
Include recovery and escalation conditions without embedding credentials or raw snapshot data.
Use the self-review rubric to assess the reasoning in your handoff after runtime checks pass.

Build the final Dispatch release with `VERSION` set to `dispatch-handoff-v1`, transfer its image into these guests, and roll both the API and worker onto that built artifact.
Verify the running release rather than changing only the workspace file.
