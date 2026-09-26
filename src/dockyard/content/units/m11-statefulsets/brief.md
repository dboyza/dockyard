# Bring back a stateful database without disposable claims

The database StatefulSet is scaled to zero and configured to delete generated claims when scaled down or deleted.
Repair `platform.yaml` so it runs one replica and explicitly retains claims for both events.
Preserve the data claim template and governing headless Service.
Apply the change and wait for `statefulset/db` to roll out.

Run `python storage-proof.py`, inspect db-0 before and after replacement, and compare Pod UID, claim name, and PV identity.
Explain why a replacement Pod can have the same name but a different UID.
Do not scale PostgreSQL beyond one replica or claim that the StatefulSet automatically replicates its database.
