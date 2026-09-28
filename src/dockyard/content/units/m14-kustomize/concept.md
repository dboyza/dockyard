## One set of manifests, several environments

Development, staging, and production usually run the same application with small differences: a namespace, a replica count, a setting.
Copying every manifest for each environment quickly drifts out of step.
**Kustomize**, built into kubectl, solves this by keeping one shared **base** and a small **overlay** per environment that describes only what differs.

```text
kustomize/
  base/                   the shared manifests plus a kustomization.yaml listing them
  overlays/
    development/
      kustomization.yaml  "use ../../base, then change these things"
    staging/
      kustomization.yaml
```

## A kustomization file

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namespace: dispatch
replicas:
- name: dispatch
  count: 2
patches:
- target:
    kind: ConfigMap
    name: dispatch-settings
  patch: |
    - op: replace
      path: /data/environment
      value: development
```

- `resources` lists files or folders to include; here, the whole base.
- `namespace` puts every resource in that namespace.
- `replicas` sets a workload’s replica count by name.
- `patches` changes specific fields. This one is a **JSON patch**: `op`, `path`, and `value`. A patch can also be a partial YAML object that is merged in.

Other common settings you will see:

- `namePrefix` or `nameSuffix` adds text to every resource name.
- `labels` adds labels to every resource.
- `images` swaps an image name or tag without editing the Deployment.
- `configMapGenerator` builds a ConfigMap from files or literal values.

## Render, review, apply

```sh
kubectl kustomize kustomize/overlays/development
kubectl apply -k kustomize/overlays/development
```

`kubectl kustomize` prints the final YAML without changing anything, so you can review it.
`kubectl apply -k` renders and applies in one step.

This lab’s manifests also contain Dockyard placeholders for the image and password, which Kustomize does not fill in.
So here you render, pass the result through the supplied `render.py`, then apply:

```sh
kubectl kustomize kustomize/overlays/development | python render.py - | kubectl apply -f -
```

That rendered output contains the practice password, so do not save it to a file.

## Checking the result

```sh
kubectl get deployment dispatch
kubectl get configmap dispatch-settings -o yaml
kubectl rollout restart deployment/dispatch
```

The environment value reaches Dispatch as an environment variable, which is only read when a container starts.
After changing it, restart the Deployment, then check Dispatch’s `/config` response.

This lab deploys only the development overlay.
The staging overlay is there for comparison; the Helm lesson deploys staging instead, so that two tools never manage the same objects.
