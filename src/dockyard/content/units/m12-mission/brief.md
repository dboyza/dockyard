## Recover the stable release, then preview the candidate

1. In `platform.yaml`, fix the stable image, the three probes, and the rolling update settings.
   The probes are startup on `/startupz`, liveness on `/healthz`, and readiness on `/readyz`.
   The rolling update uses two replicas, `maxUnavailable: 0`, and `maxSurge: 1`, and keeps the twelve-second warmup.
2. Run one candidate replica from the release-2 image and fix the preview Service’s selector.
3. Check the main Service has three ready endpoints and the preview reaches only the candidate.
4. Run `python termination-proof.py` and confirm a clean exit.
5. Choose **Check work**.

Keep PostgreSQL’s storage and the working configuration and identity files; do not rebuild the cluster.

Write a runbook for the next person.
Include the symptoms you found, what you changed, and which release each Service returned.
Include when you would promote or abort, and the commands to roll back.
Explain why rolling back the image would not undo a bad database change.
Say how you would use the Module 11 backup and restore if data were affected.
