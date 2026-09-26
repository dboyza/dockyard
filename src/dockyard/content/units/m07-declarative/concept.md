# A context selects where a command goes

A kubeconfig contains clusters, credentials, and contexts.
A context selects one cluster and identity plus an optional default namespace.
Dockyard gives each lab its own kubeconfig through `KUBECONFIG`; this does not modify your default file.
Always inspect the current context before applying a manifest copied from another task.

## Worked example

```sh
kubectl config current-context
kubectl config view --minify
kubectl api-resources --api-group=apps
kubectl explain deployment.spec.replicas
python render.py deployment.yaml | kubectl diff -f -
sh run.sh
kubectl rollout status deployment/dispatch --timeout=90s
```

`diff` returns status 1 when differences exist, which is useful information rather than an apply failure.
`apply` changes desired state; `rollout status` waits for the Deployment controller's observed result.
Server-side validation can reject unsupported fields before any healthy Pod is created.

## API versions evolve

A manifest's `apiVersion` selects the schema and endpoint used to represent an object.
An API can be deprecated and later removed; retaining an old YAML file does not retain that endpoint on an upgraded server.
Deployments use `apps/v1` on this cluster.
The removed `extensions/v1beta1` Deployment API cannot be restored by adding a namespace or retrying apply.
Read the deprecation guide, inspect `api-resources`, and migrate both the version and fields when necessary.
A dry run with `kubectl apply --dry-run=server -f FILE` validates against the actual server without persisting the change.
