## Get the API Pods ready again

Make both API Pods Ready, so the existing `dispatch` Service reaches them and jobs can be submitted.

- Keep startup on `/startupz`, liveness on `/healthz`, and readiness on `/readyz`.
- Keep the database’s storage and its original job.
- Do not remove the probes, or make the Service send traffic to unready Pods.

In your notes, record the first observation that pointed at the cause, your fix, and a check you could run after future changes to catch it.
