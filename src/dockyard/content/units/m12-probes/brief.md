# End the warmup restart loop

The starter has no startup probe, uses dependency readiness for liveness, and uses process health for readiness.
Repair the API container in `platform.yaml` with startup `/startupz`, liveness `/healthz`, and readiness `/readyz`, all on port 8080.
Give startup at least thirty seconds of failure budget and preserve the supplied twelve-second warmup.
Keep a twenty-second or longer termination grace period.
Apply the manifest and wait for two stable replicas to become available.

Run `python termination-proof.py`, inspect `kubectl logs termination-proof`, and confirm a successful process exit after the termination event.
Explain why a healthy HTTP process waiting on a failed database should leave ready endpoints without being repeatedly restarted.
