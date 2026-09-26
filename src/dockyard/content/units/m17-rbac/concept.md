# Authenticate an identity, then authorize an operation

Authentication establishes who made a request.
Authorization decides whether that identity may perform a verb on a resource in a scope.
A ServiceAccount identifies a workload; it does not grant application permissions by itself.
A Role declares namespaced permissions, and a RoleBinding grants those permissions to named subjects.
A ClusterRole can be reused through a RoleBinding without granting access across the whole cluster.
A ClusterRoleBinding grants its referenced permissions at cluster scope.

The supplied inventory process needs to read Pods in dispatch so it can report workload membership.
Its projected short-lived service account token authenticates ordinary HTTPS requests to the Kubernetes API using the mounted cluster CA.
The API and worker do not call the Kubernetes API and disable automatic token mounting.
Their database credential is a different identity for a different service.

For example, a reporting process that only reads ConfigMaps could use this Role rule:

```yaml
rules:
- apiGroups: [""]
  resources: [configmaps]
  verbs: [get, list]
```

The empty API group means core resources; Deployments belong to apps.
Reading pods does not automatically grant pods/log or pods/exec, and access to a subresource needs an explicit rule where required.
Avoid wildcards when the required operations are known.
Permission to create workloads can also create indirect paths to credentials or privileged behavior, so least privilege requires more than denying direct Secret reads.

```sh
kubectl get role dispatch-pod-reader -o yaml
kubectl get rolebinding dispatch-pod-reader -o yaml
kubectl auth can-i list pods --as=system:serviceaccount:dispatch:dispatch-reader
kubectl auth can-i get secrets --as=system:serviceaccount:dispatch:dispatch-reader
```

The lab's administrator identity can impersonate the practice account for the can-i check.
The assessment also makes real HTTPS calls using the inventory process's actual token and expects successful Pod reads but forbidden Secret and other-namespace reads.
A 403 is evidence of authorization denial; a timeout or certificate error is a different failure and does not count as that denial.
Inspect the token's presence only where needed and never copy it into notes or Git.
