## Stop the restart loop

The API has no startup probe, uses `/readyz` for liveness, and `/healthz` for readiness, so it restarts before it can finish warming up.

1. Watch the Pods and their events to see the restart loop.
2. In `platform.yaml`, give the `api` container a startup probe on `/startupz`, liveness on `/healthz`, and readiness on `/readyz`, all on port 8080.
3. Give the startup probe at least thirty seconds of budget. Keep the twelve-second warmup, and a `terminationGracePeriodSeconds` of twenty or more.
4. Run `sh run.sh` and wait for two stable replicas.
5. Run `python termination-proof.py`, then `kubectl logs termination-proof`, and confirm a clean exit.
6. Choose **Check work**.

In your notes, explain why an API that is running but cannot reach its database should stop getting traffic, but not be restarted.
