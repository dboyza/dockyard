## Installing applications as packages

**Helm** is a package manager for Kubernetes.
Its packages are called **charts**: a folder of templated manifests plus a `values.yaml` file of settings.
When you install a chart, Helm fills the templates in with values and creates the objects.
Each installation is a named **release**, and every change to it is a numbered **revision** you can inspect and roll back.

## The commands you need

With public charts, you first add a **repository**, a website that hosts charts:

```sh
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo nginx
```

This lab works offline with a local chart in `charts/dispatch`, but the other commands are the same:

```sh
helm install NAME CHART -n NAMESPACE --create-namespace
helm upgrade --install NAME CHART -n NAMESPACE -f my-values.yaml --set api.replicas=2
helm list -n NAMESPACE
helm status NAME -n NAMESPACE
helm history NAME -n NAMESPACE
helm get values NAME -n NAMESPACE
helm rollback NAME REVISION -n NAMESPACE
helm uninstall NAME -n NAMESPACE
helm show values CHART
helm template NAME CHART -f my-values.yaml
```

- `-f FILE` supplies values from a file; `--set key=value` sets one value on the command line. Later values win over earlier ones.
- `upgrade --install` installs if the release does not exist, and upgrades it otherwise.
- `show values` prints a chart’s default values, so you know what you can set.
- `template` renders the manifests locally without installing anything.
- `--wait` makes install and upgrade wait until the new objects are ready.

## This lab

The chart deploys Dispatch into the `staging` namespace as a release called `dispatch`.
Its values set the API replica count and environment.
The image name and database password come from a private values file that `helm-values.py` writes outside your workspace, so the chart itself never contains the password.

```sh
python helm-values.py
helm lint charts/dispatch -f values-practice.yaml -f "$DOCKYARD_STORAGE/helm-values.json"
helm history dispatch -n staging
helm get values dispatch -n staging
```

`helm template` output includes the rendered Secret, and `helm get values` prints every value supplied to the release, including the practice password.
Look at them on screen, but do not copy them into notes or files.
In real deployments, this is one reason teams keep passwords out of Helm values altogether, for example by creating the Secret separately or using an external secret manager.

Revision 1 was healthy.
Revision 2 set `api.replicas` to 0, and Helm still reported it as deployed, because zero ready copies out of zero requested satisfies Helm’s wait.
A successful Helm command is not proof the application is serving.

## Rolling back

```sh
helm rollback dispatch 1 -n staging --wait --timeout 120s
kubectl rollout status deployment/dispatch -n staging --timeout=120s
```

A rollback creates a *new* revision that reuses revision 1’s manifests and values; history is kept.
It fixes the running release, but not your values file.
`values-practice.yaml` still says 0 replicas, so the next ordinary upgrade would break it again.
Fix the file too.

Like any rollback, this only changes Kubernetes objects; it would not undo database changes.
