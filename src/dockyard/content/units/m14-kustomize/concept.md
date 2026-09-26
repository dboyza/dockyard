# Transform a shared base without copying an environment

Kustomize composes ordinary Kubernetes YAML and applies declared transformations.
A base contains reusable resources; an overlay selects that base and expresses environment-specific changes.
`kubectl kustomize` renders the final resources, while `kubectl apply -k` renders and applies them.
Rendering first lets you review the exact namespace, selectors, replicas, and configuration before changing a cluster.

The supplied base includes Dispatch, its dependencies, identities, and maintenance workloads.
The development overlay selects namespace dispatch, two API replicas, and the development environment value.
The staging example demonstrates a separate namespace and three replicas without copying the shared base.
This lab deploys only development; the next lab gives staging to Helm so two tools never compete for the same resources.

```sh
kubectl kustomize kustomize/overlays/development
kubectl kustomize kustomize/overlays/development | python render.py - | kubectl apply -f -
kubectl get deployment dispatch -o yaml
kubectl get configmap dispatch-settings -o yaml
```

The second command also resolves Dockyard's documented image and credential placeholders.
That small supplied renderer is specific to these local exercises; substitution of environment variables is not an implicit Kustomize feature.
Avoid saving its concrete Secret output in Git or a portfolio export.

Replica transforms change workload counts without editing the base.
A targeted JSON patch replaces the ConfigMap environment field.
A namespace transform updates recognized namespace references, but arbitrary strings and custom fields still require deliberate configuration.
ConfigMap environment variables are captured when a container starts, so applying a new value alone does not update an existing process.
Roll the API after changing that value, then compare the actual `/config` response with rendered intent.
