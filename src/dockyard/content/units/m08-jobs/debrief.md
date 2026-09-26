# Explain the lifecycle choices

Trace one submitted job from the API through PostgreSQL and Redis to the worker that completed it.
Explain which state is durable within the current Pod lifetime and which would be lost after Pod replacement.
Compare Deployment availability, DaemonSet node coverage, and Job completion as three distinct success conditions.

Identify a failure that the Kubernetes controller can repair and a configuration failure it can only keep retrying.
For a CronJob, distinguish template correctness, one observed successful run, and reliable operation over many schedules.
Record the evidence you would collect before increasing replicas in response to slow processing.
