# Repair the envelope, then drain a worker

Repair required affinity and the taint toleration in `platform.yaml`, the HPA target in `autoscale.yaml`, and minAvailable in `capacity.yaml`.
Keep the two dedicated application workers, real CPU requests and limits, namespace budgets, two-to-four HPA range, and topology spread.
Wait for four available stable API replicas under the supplied load.

Run `python drain-proof.py` from the scoped terminal.
The script uses the eviction API, keeps two replicas protected, samples readiness, restores node schedulability, and records the replaced Pod identities.
Inspect its output and the final Pod distribution.
If the drain is blocked, diagnose the budget and placement instead of adding force flags or deleting the budget.

Write a maintenance note with the node, observed samples, replacement evidence, remaining capacity, and the local failure-domain limitation.
Preserve the database claim and the dedicated dependency placement throughout the rehearsal.
