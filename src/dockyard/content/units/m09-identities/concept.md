# Authentication identifies; authorization decides

A ServiceAccount gives a workload a namespaced Kubernetes identity.
Creating it does not grant arbitrary API permissions.
A Role describes namespaced permissions, and a RoleBinding grants those permissions to its subjects.
The identity string includes the namespace: `system:serviceaccount:dispatch:dispatch-reader`.
An equally named ServiceAccount in another namespace is a different identity.

Modern Pod credentials use projected, time-limited tokens that Kubernetes can rotate.
The token is a credential, not ordinary lesson evidence, so do not paste it into notes or logs.
The supplied inventory client needs to list Pods in `dispatch`; the business API and workers do not need Kubernetes API access.
Their `dispatch-app` account disables automatic token mounting.

## Worked example

```sh
kubectl get serviceaccount dispatch-reader
kubectl describe role dispatch-pod-reader
kubectl describe rolebinding dispatch-pod-reader
kubectl auth can-i list pods --as=system:serviceaccount:dispatch:dispatch-reader -n dispatch
kubectl auth can-i list secrets --as=system:serviceaccount:dispatch:dispatch-reader -n dispatch
```

These authorization queries are useful, but a complete check also sends a request from the inventory Pod with its own mounted token and CA certificate.
The expected outcomes are a successful Pod list, a denied Secret list, and a denied Pod list in `kube-system`.
A 403 means the request reached authorization and was forbidden; a timeout or connection failure is a different layer.
Detailed least-privilege auditing and broader RBAC risks are revisited in the security phase.
