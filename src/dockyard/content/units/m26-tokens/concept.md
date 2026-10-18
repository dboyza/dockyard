## Every Pod has an identity

Every Pod runs as a **ServiceAccount**, the identity it uses when it talks to the Kubernetes API.
If a Pod does not name one, it runs as the namespace's `default` ServiceAccount.
You gave Dispatch's Pods their own identity earlier in the course; this lesson is about cleaning up a namespace where that was never done.

To let a Pod prove its identity, Kubernetes mounts a **token** into it at `/var/run/secrets/kubernetes.io/serviceaccount/token`.
Anyone who can read that file, including an attacker who has taken over the container, can call the API with the Pod's permissions.
That leads to three habits:

- Give each workload that needs the API its own ServiceAccount, with only the permissions it needs.
- Do not mount a token into Pods that never call the API.
- Do not keep long-lived token Secrets lying around.

```figure
service-account-tokens
```

## Mounted tokens

The token Kubernetes mounts today is a **bound token**.
It expires after about an hour, and the kubelet replaces it before then.
It becomes invalid when its Pod is deleted.
It arrives through a projected volume that Kubernetes adds to the Pod automatically.

Setting `automountServiceAccountToken: false` stops that volume being added.
It can be set on a ServiceAccount, which covers every Pod using it, or in a Pod's `spec`, which overrides the ServiceAccount's setting for that Pod.
Because the volume is added when a Pod is created, existing Pods keep their tokens until they are replaced.

## Legacy token Secrets

Before bound tokens, Kubernetes stored a token for every ServiceAccount in a Secret of type `kubernetes.io/service-account-token`.
Those tokens **never expire**.
Kubernetes no longer creates them automatically, but anyone can still create one, and old clusters often have them.
Find them with:

```sh
kubectl get secrets -n reports --field-selector type=kubernetes.io/service-account-token
```

A copied legacy token keeps working for as long as the Secret exists, so deleting the Secret is the way to revoke it.

## Least privilege for the builder

`report-builder` reads one ConfigMap, `report-settings`, from the API.
It does not need the `edit` ClusterRole, which can change almost everything in the namespace, including Secrets.
A Role can name individual objects with `resourceNames`:

```yaml
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["report-settings"]
  verbs: ["get"]
```

```figure
least-privilege-identity
```

Check what an identity can do by asking the API server as that identity:

```sh
kubectl auth can-i --list -n reports --as=system:serviceaccount:reports:default
kubectl auth can-i get configmap/report-settings -n reports --as=system:serviceaccount:reports:report-builder
```

## Fix it

The workspace file `reports.yaml` describes the namespace as it was handed over.
Edit it, and remember that `kubectl apply` adds and updates objects but never deletes ones you remove from the file.

1. Remove the `reports-default-edit` RoleBinding and the `default-token-legacy` Secret from `reports.yaml`, and delete them from the cluster with `kubectl delete`.
2. Add a `default` ServiceAccount with `automountServiceAccountToken: false`.
3. Add a `report-builder` ServiceAccount, a Role that can only `get` the `report-settings` ConfigMap, and a RoleBinding between them.
4. Set `serviceAccountName: report-builder` in the builder's Pod template.
5. Apply with `python render.py reports.yaml | kubectl apply -f -`, then run `kubectl rollout restart deployment/report-viewer -n reports` so the viewer is recreated without a token.

`kubectl logs -n reports deploy/report-builder` should keep showing `report_built` events.

## If something goes wrong

- **The builder logs `report_failed` with `HTTPError`**: its identity cannot read the ConfigMap. Check the RoleBinding's subject names the `report-builder` ServiceAccount in `reports`, and the Role's `resourceNames` is spelled exactly.
- **The viewer still has a token**: it was created before you changed the default ServiceAccount. Restart its Deployment.
- **The legacy Secret came back**: it is still in `reports.yaml`, and your last apply recreated it.
