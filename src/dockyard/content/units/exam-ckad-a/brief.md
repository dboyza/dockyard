# Dispatch release assessment

Complete the eight weighted tasks in the exam workspace.
Use the ordinary external terminal and retain the supplied application source and seeded state.

## 1. Build the release artifact (20%)

Build the supplied application as release `dispatch-exam-a` using the workspace VERSION file.
Repair its Dockerfile so the ordinary image entry point runs the API as a nonroot user.
Load the resulting image into this owned kind cluster and run two Dispatch API replicas from it.
Preserve the supplied API and worker application behavior.
You may use a new local image tag or replace the existing practice tag and deliberately restart the workload.

## 2. Consume the accepted configuration (10%)

Make both API replicas report environment `assessment` and banner `Dispatch release accepted` through their actual `/config` endpoint.
Use the existing `dispatch-settings` ConfigMap as the environment and mounted-file source.
Do not change the supplied application code to hard-code these values.

## 3. Separate health signals (15%)

Keep a startup probe on `/startupz` with at least a 30-second failure budget, liveness on `/healthz`, and dependency-aware readiness on `/readyz`.
Use the actual API listener on 8080.
The released replicas must finish startup and report their database and queue ready.

## 4. Schedule a release audit (10%)

Configure CronJob `release-audit` for 02:17 every day in UTC, prevent overlapping executions, and leave it unsuspended.
Its supplied command requests the live Service health endpoint.
Create Job `release-audit-proof` from this CronJob and demonstrate successful completion with the `dispatch-exam-a` release in its output.

## 5. Recover the stable request path (15%)

Retain Service `dispatch` on port 8080 and restore its route to exactly the two ready API backends.
A fresh submitted job must complete in a worker and have the same result stored in PostgreSQL.
Do not bypass the Service with a Pod address or publish unready backends.

## 6. Persist the report workspace (10%)

Mount the original `reports` ReadWriteOnce claim at `/archive` in Deployment `reporter`.
The existing emptyDir mount does not meet the persistence requirement.
Keep one running reporter and the original claim identity.
A fresh file written through that mount must be readable from a second consumer of the same claim.
Also preserve the original Dispatch namespace, database claim, and seeded job.

## 7. Connect initialization and log observation (10%)

Create Pod `audit-tail` with init container `seed` and ordinary containers `producer` and `tailer`.
All three must share an emptyDir mounted at `/shared`.
The init container writes `release audit ready` into `/shared/events` before completing successfully.
The producer appends `dispatch-exam-a` and remains running.
The tailer emits the file's existing and newly appended lines to its own container log.
Use the supplied Python image and keep both ordinary containers running.
The observer will append a fresh marker from the producer and require it to appear in the tailer's log.

## 8. Constrain an audit endpoint (10%)

Restrict ingress to the `audit-target` Pods on TCP 8080 to Pods in the same namespace with `role: audit-reader`.
The supplied `audit-reader` must connect and `audit-outsider` must be denied.
Keep the target and both clients running; a stopped client does not establish a denied connection.
Do not change the clients' labels or replace their processes with a fabricated success response.
