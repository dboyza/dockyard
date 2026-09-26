# A chart is a package; a release is an installation

Helm renders chart templates using values and release metadata, then manages an installation of those resources.
The supplied local chart contains the same Dispatch components you have already operated.
Its values control API replica count and environment; image digests and the database password come from a private lab values file.
The chart source contains placeholders, never the generated credential.

```sh
python helm-values.py
helm lint charts/dispatch -f values-practice.yaml -f "$DOCKYARD_STORAGE/helm-values.json"
helm template dispatch charts/dispatch -n staging -f values-practice.yaml -f "$DOCKYARD_STORAGE/helm-values.json"
helm history dispatch -n staging
helm get values dispatch -n staging
```

Template output includes the rendered Secret, so inspect it locally without committing or exporting it.
`release.sh` performs upgrade --install with the supplied values and waits for Kubernetes readiness.
Helm release records live as Secrets in the release namespace, and Dockyard gives Helm private local cache/config/data directories.
A successful command means its configured wait conditions passed, not that the application is semantically correct.
A Deployment deliberately scaled to zero can produce a deployed release while serving no requests.

The starter installs a working revision, then upgrades with api.replicas=0.
Use history and the live Deployment to identify the regression.
Rollback creates a new release revision using an earlier revision's resources and values; it does not erase history.
Correct the source values too so the next ordinary upgrade does not reintroduce the outage.

```sh
helm rollback dispatch 1 -n staging --wait --timeout 120s
kubectl rollout status deployment/dispatch -n staging --timeout=120s
```

A rollback does not undo external effects such as a database schema migration.
This exercise changes only replica count and retains the database claim.
