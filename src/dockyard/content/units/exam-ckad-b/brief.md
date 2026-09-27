# Dispatch delivery assessment

Complete the eight weighted outcomes while preserving the stable application and its data.

## 1. Pin the accepted private artifact (15%)

The private registry and its pull credential are healthy.
Resolve the tested `dispatch:incident` image in the registry named in `registry.txt` and pin both stable API replicas to its immutable manifest digest.
Keep authenticated pull resolution with imagePullPolicy Always.
The actual running release must remain the supplied stable application.
Use the lab's DOCKYARD_REGISTRY_PASSWORD only for this owned registry; do not publish credentials.

## 2. Restore dependency access and remove the API token (15%)

Repair the stable API's projected database credential path so its dependency-aware readiness succeeds.
The correct existing Secret is mounted at `/var/run/dispatch` with a `password` key.
Disable automatic service-account token mounting for these application Pods, which do not call the Kubernetes API.
A fresh Dispatch job must complete through the stable Service and persist its result.

## 3. Fit the workers into a deliberate resource budget (10%)

Run two available workers with positive CPU requests no larger than their limits, and CPU limits of at most 500m per worker.
Use memory requests of at least 32Mi, requests no larger than limits, and memory limits of at most 256Mi.
The running containers must have the effective cgroup memory limit.
Do not replace the supplied worker process or scale it away.

## 4. Apply production metadata through Kustomize (10%)

Complete `release/overlays/production` so the rendered configuration and live `metadata-reader` consume environment `production` and release `dispatch-approved-b`.
Keep the base reusable and use an overlay ConfigMap generator merge for the production values.
Apply the overlay, preserving its generated ConfigMap reference in the workload.
The reader must serve both values from its mounted files.

## 5. Recover a controlled preview rollout (15%)

Repair Deployment `preview-api` using the supplied local image `$DOCKYARD_IMAGE-preview`.
Run two ready API replicas serving release `dispatch-preview-b`.
Configure a rolling update with zero unavailable replicas and one surge replica, preserving the stable Deployment separately.
Both replicas must run the supplied API and become dependency-ready.

## 6. Recover the report listener (10%)

Diagnose the `report-listener` process from its logs and environment.
Configure its PORT as 8090 and retain its supplied Python HTTP server.
Keep Service `reports` on port 8080, routing to the actual 8090 listener.
An ordinary HTTP request through the Service must succeed.

## 7. Restore the accepted report into its existing claim (10%)

Restore the exact bytes of `report-backup.json` as `/archive/report.json` in Deployment `report-cache`.
Preserve and use its original `report-cache` claim at `/archive`.
Keep the backup unchanged, and preserve the original Dispatch namespace, database claim, and seeded application row.
The recovered report is separate from the application's database recovery contract.

## 8. Separate stable and preview traffic (15%)

Repair Service `preview` to select exactly the ready preview API replicas.
Keep Service `dispatch` selecting exactly the ready stable API replicas.
Actual requests through the two Services must return their respective stable and preview release identities.
Retain both Services on port 8080.
