# Dispatch delivery assessment

Eight tasks, each with its weight.
Everything is in namespace `dispatch` unless a task says otherwise.
Keep the stable application, its database and claim, and the job already stored in it.

## 1. Deploy the approved image by digest (15%)

The private registry and its pull Secret are working.
The registry address is in `registry.txt`; the username is `learner`, and the password is in the variable `DOCKYARD_REGISTRY_PASSWORD`.

- Find the digest of image `dispatch:incident` in that registry.
- Set both replicas of Deployment `dispatch` to that image by digest (`REGISTRY/dispatch@sha256:...`), keeping `imagePullPolicy: Always`.

Use the password only through the variable, for example with `docker login --password-stdin`, and never paste it into files, manifests, or notes.

## 2. Fix the database password path and remove the API token (15%)

The API reads its database password from the file named in its `DB_PASSWORD_FILE` environment variable.
The correct Secret is already mounted at `/var/run/dispatch`, with the password under key `password`.

- Point the API at the right file so its `/readyz` reports ready.
- The API never calls the Kubernetes API, so stop Kubernetes mounting a ServiceAccount token into its Pods.

A new job sent through Service `dispatch` must complete and be saved.

## 3. Set worker resources (10%)

Deployment `worker` must run two available replicas of the existing worker, each with:

- a CPU request greater than zero, a CPU limit of at most `500m`, and the request no larger than the limit;
- a memory request of at least `32Mi`, a memory limit of at most `256Mi`, and the request no larger than the limit.

## 4. Finish a Kustomize overlay (10%)

Complete `release/overlays/production` in the workspace.

- Use a `configMapGenerator` in the overlay that merges into the base's generated ConfigMap, setting `environment` to `production` and `release` to `dispatch-approved-b`.
- Leave `release/base` unchanged so other overlays can reuse it.
- Apply the overlay with `kubectl apply -k`.

Deployment `metadata-reader` must use the generated ConfigMap and serve both values.

## 5. Fix the preview Deployment (15%)

Deployment `preview-api` must run the local image `$DOCKYARD_IMAGE-preview`.

- Run two ready replicas serving release `dispatch-preview-b`.
- Use a rolling update with `maxUnavailable: 0` and `maxSurge: 1`.
- Do not change Deployment `dispatch`.

## 6. Fix the report listener (10%)

Deployment `report-listener` runs a Python web server that reads its port from the `PORT` environment variable.

- Set `PORT` to `8090`, keeping the same server.
- Keep Service `reports` on port 8080, sending traffic to port 8090.

An HTTP request to `http://reports:8080/` from inside the cluster must succeed.

## 7. Restore a report into its volume (10%)

Deployment `report-cache` mounts PersistentVolumeClaim `report-cache` at `/archive`.

- Copy the workspace file `report-backup.json`, byte for byte, to `/archive/report.json` in that volume.
- Keep the same claim, and leave `report-backup.json` unchanged.

Also keep the namespace, the database's claim, and the job stored in it.

## 8. Separate stable and preview traffic (15%)

Both Services keep port 8080.

- Service `preview` must send traffic to exactly the ready `preview-api` Pods.
- Service `dispatch` must send traffic to exactly the ready stable API Pods.

Requests through each Service must return its own release.
