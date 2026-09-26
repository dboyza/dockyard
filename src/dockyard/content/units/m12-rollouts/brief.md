# Restore the known release and its update budget

Inspect the failed image and the prior ReplicaSet before making changes.
Recover the Deployment using rollout undo or an equivalent explicit image repair.
Update `platform.yaml` to use `${DOCKYARD_IMAGE}` and configure maxUnavailable 0 with maxSurge 1.
Render and apply the corrected manifest, then wait for two available stable replicas and query the live release.

Retain the failed ReplicaSet in history so the difference remains inspectable.
Do not delete and recreate the entire Deployment to erase the evidence.
Record which command recovered live state and which edit prevented the broken release from returning on the next apply.
