# Dispatch release assessment

Eight tasks, each with its weight.
Everything is in namespace `dispatch` unless a task says otherwise.
Keep the existing application code, the database and its claim, and the job already stored in it.

## 1. Build and run the release image (20%)

The workspace `VERSION` file already says `dispatch-exam-a`.

- Fix the workspace `Dockerfile` so the image starts the API normally and runs it as a non-root user.
- Build the image, load it into this lab's kind cluster, and run Deployment `dispatch` with two replicas of it.

You may use a new tag, or rebuild the existing tag and restart the Deployment.

## 2. Configure the release from a ConfigMap (10%)

Both API replicas must report environment `assessment` and banner `Dispatch release accepted` from their `/config` endpoint.

- The API reads the environment from an environment variable and the banner from a mounted file, both from ConfigMap `dispatch-settings`.
- Change the configuration, not the application code.

## 3. Configure health probes (15%)

For the `api` container in Deployment `dispatch`, on port 8080:

- a startup probe on `/startupz` that allows at least 30 seconds before failing (`failureThreshold` × `periodSeconds` ≥ 30);
- a liveness probe on `/healthz`;
- a readiness probe on `/readyz`.

Both replicas must finish starting up and report ready.

## 4. Schedule a release audit (10%)

Update CronJob `release-audit`:

- run at 02:17 every day, with `timeZone` set to UTC;
- never run two audits at the same time;
- not suspended.

Then create Job `release-audit-proof` from the CronJob.
It must complete successfully, and its log must show release `dispatch-exam-a`.

## 5. Fix the Service (15%)

Service `dispatch` must keep port 8080 and send traffic to exactly the two ready API Pods.

- A new job submitted through the Service must be processed by a worker and saved in PostgreSQL.
- Do not bypass the Service or make it include Pods that are not ready.

## 6. Give the reporter persistent storage (10%)

Deployment `reporter` mounts an `emptyDir` at `/archive`.

- Mount the existing PersistentVolumeClaim `reports` at `/archive` instead.
- Keep one running reporter, and keep the same claim; do not create a new one.

A file written to `/archive` must be readable by another Pod that mounts the same claim.
Also keep the namespace, the database's claim, and the job stored in it.

## 7. Create a Pod with an init container and a log sidecar (10%)

Create Pod `audit-tail` with an `emptyDir` volume mounted at `/shared` in all three containers.
Use the Dispatch image, `$DOCKYARD_IMAGE` with `imagePullPolicy: Never`, which includes Python; Check work runs Python inside `producer`.

- init container `seed` writes the line `release audit ready` to `/shared/events`, then exits successfully;
- container `producer` appends the line `dispatch-exam-a` to `/shared/events` and keeps running;
- container `tailer` prints `/shared/events` to its log, including lines added later, and keeps running.

Check work will append a new line through `producer` and expect it to appear in the `tailer` log.

## 8. Restrict access with a NetworkPolicy (10%)

Only Pods in `dispatch` labeled `role: audit-reader` may connect to the `audit-target` Pods on TCP port 8080.

- The existing `audit-reader` Pod must still connect, and `audit-outsider` must be refused.
- Keep all three Deployments running and do not change their labels or commands.
