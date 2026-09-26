# Define what a safe release proved

Separate application health, dependency readiness, startup time, and graceful termination.
Describe the available-replica budget during an update and what observations would make you stop promotion.
Compare stable and candidate release identities through both shared and preview Services.

Explain why Pod-count proportions are not an exact traffic-weighting mechanism and why an application rollback cannot reverse an incompatible database migration.
Record a release and rollback runbook with concrete readiness, traffic, data, and recovery checks.
The local exercise verifies these mechanisms, not production zero-downtime guarantees under arbitrary load.
