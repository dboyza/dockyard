# Deliver the workload checkpoint

Repair the supplied workload manifests and demonstrate these outcomes:

- Two API replicas and two worker replicas serve and process real Dispatch jobs.
- A healthy `dispatch-node-agent` DaemonSet covers every eligible node.
- `dispatch-maintenance` schedules maintenance every five minutes with `Forbid` concurrency and bounded retries.
- A Job named `maintenance-proof` created from that template completes and records a real database observation.
- `WORKLOADS.md` explains why each controller was chosen, what a retry can repeat, and when the current database data would disappear.

No exact repair command sequence is required.
The automated assessment verifies live workload and application behavior; your written tradeoffs are for self-review and the mission portfolio.
