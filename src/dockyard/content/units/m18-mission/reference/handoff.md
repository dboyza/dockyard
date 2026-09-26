# Dispatch recovery handoff

## Failure

The primary database was stopped while the frontend policy selected a retired client label.
The application image also contained an unused vulnerable dependency, and the original database credential still required revocation.
These were separate availability, artifact, and credential concerns.

## Recovery

Restore the trusted frontend peer, authenticate and decrypt backup.json with the private lab key, and restore into db-recovery's new claim.
Verify the saved completed job before switching the db Service to recovery: restored.
Preserve data-db-0 and leave the original StatefulSet scaled to zero.
Rotate the database password and refresh the API and worker, then rebuild without unused PyJWT and replace both consumers.

## Validation

Inspect kubectl get pvc,pv and the db Service selector to record the distinct original and restored volume identities.
The frontend must show the original completed marker and successfully process a new job.
The old database password must fail while the current Secret succeeds against the same server.
Compare scan-before.json, scan-after.json, and their CycloneDX inventories using the recorded scanner database date and image identities.
The checker also rejects a deliberately altered encrypted backup tag.

## Remaining risks

Removing the teaching dependency does not remediate all base-image findings.
Triage the remaining scan results and plan a tested base-image update.
This practice administrator role needs a narrower production role design, and database transport TLS and etcd encryption remain separate controls.
Keep the backup key outside exported source, with a separately tested custody and recovery procedure.

## Rollback

Retain both volumes while deciding which database has authoritative data.
Do not blindly switch traffic back to the old primary after accepting new writes on the restored copy.
Quiesce writes, reconcile data, verify the chosen target, and only then change the Service selector.
Never overwrite the original volume merely to make a rollback command shorter.
