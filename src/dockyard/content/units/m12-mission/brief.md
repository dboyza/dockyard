## Recover the stable release, then preview the candidate

1. In `platform.yaml`, fix the stable image, the three probes (startup on `/startupz`, liveness on `/healthz`, readiness on `/readyz`), and the rolling update settings: two replicas, `maxUnavailable: 0`, `maxSurge: 1`, keeping the twelve-second warmup.
2. Run one candidate replica from the release-2 image and fix the preview Service’s selector.
3. Check the main Service has three ready endpoints and the preview reaches only the candidate.
4. Run `python termination-proof.py` and confirm a clean exit.
5. Choose **Check work**.

Keep PostgreSQL’s storage and the working configuration and identity files; do not rebuild the cluster.

Write a runbook covering the symptoms you found, what you changed, which release each Service returned, when you would promote or abort, the commands to roll back, and why rolling back the image would not undo a bad database change.
Say how you would use the Module 11 backup and restore if data were affected.
