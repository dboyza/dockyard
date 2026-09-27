# Incident report

After a port-label cleanup, both API processes finish startup and answer direct health requests, but the public Service has no usable backends.

Restore two ready API replicas and actual job submission through the existing Service.
Keep startup on `/startupz`, liveness on `/healthz`, and dependency-aware readiness on `/readyz`.
Preserve the database claim and its original job.
Do not disable probes or publish unready addresses to make the endpoint list look healthy.

Write a short account of the first discriminating observation, the repair, and a regression check.
Use the debrief as a self-review rubric; prose is not automatically graded.
