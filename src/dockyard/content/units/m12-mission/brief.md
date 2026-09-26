# Recover stable service, then validate the candidate

Repair the stable image, startup/liveness/readiness configuration, and rolling update budget in `platform.yaml`.
Keep two stable replicas, maxUnavailable 0, maxSurge 1, and the supplied warmup interval.
Run one candidate replica from the separately built release-2 image and repair the preview Service selector.
Verify the shared Service's three ready endpoints and the preview's candidate-only response.
Run the isolated termination proof and inspect the successful SIGTERM exit.

Preserve PostgreSQL storage and the working configuration and identity manifests.
Do not recreate the entire cluster to hide the failure.
Write a runbook describing initial symptoms, repairs, observed release identities, promotion criteria, abort commands, and database rollback limitations.
Include how you would use the independent backup procedure from Module 11 if the failure affected data rather than only application rollout.
