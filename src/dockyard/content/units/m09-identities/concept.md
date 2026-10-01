## Who is this Pod, and what may it do?

Most applications never talk to the Kubernetes API.
Some do: a dashboard that lists Pods, an operator, a CI tool.
Kubernetes answers two separate questions for every API request:

1. **Authentication**: who is making this request?
2. **Authorization**: is that identity allowed to do this?

## ServiceAccounts are identities for Pods

A **ServiceAccount** is an identity a Pod uses when it calls the API.
Each Pod runs as one ServiceAccount, set with `serviceAccountName` in its spec, or `default` if none is given.
Kubernetes gives the Pod a short-lived **token** file proving that identity, at `/var/run/secrets/kubernetes.io/serviceaccount/token`.

A ServiceAccount’s full name includes its namespace:

```text
system:serviceaccount:dispatch:dispatch-reader
```

So `dispatch-reader` in another namespace is a completely different identity.

Pods that never call the API should not carry a token at all.
Setting `automountServiceAccountToken: false` stops Kubernetes mounting it; Dispatch’s API and workers use a `dispatch-app` account with that setting.

Treat tokens as passwords: never paste one into notes or logs.

## RBAC decides what an identity may do

A new ServiceAccount can do almost nothing.
Permissions come from **RBAC**, role-based access control:

- A **Role** lists allowed actions in one namespace: which **verbs** (`get`, `list`, `watch`, `create`, `delete`...) on which **resources** (`pods`, `secrets`...).
- A **RoleBinding** gives a Role to one or more **subjects**: users, groups, or ServiceAccounts.

Both are needed.
A perfect Role that is bound to the wrong subject grants nothing.
(ClusterRoles and ClusterRoleBindings do the same across the whole cluster; the security module covers them.)

## Creating them quickly

These commands are worth knowing by heart for the exams:

```sh
kubectl create serviceaccount demo-reader
kubectl create role demo-pod-reader --verb=get,list,watch --resource=pods
kubectl create rolebinding demo-pod-reader --role=demo-pod-reader --serviceaccount=dispatch:demo-reader
```

Note the `NAMESPACE:NAME` format in `--serviceaccount`.
As always, add `--dry-run=client -o yaml` to see the YAML instead.

For a quick manual test, you can ask for a short-lived token for any ServiceAccount:

```sh
kubectl create token demo-reader --duration=10m
```

It prints a token that expires after ten minutes.
Kubernetes does not store it, so you cannot list or delete it; it simply stops working when it expires.

## Ask Kubernetes directly

`kubectl auth can-i` asks whether an identity may do something, pretending to be it with `--as`:

```sh
kubectl auth can-i list pods --as=system:serviceaccount:dispatch:dispatch-reader -n dispatch
kubectl auth can-i list secrets --as=system:serviceaccount:dispatch:dispatch-reader -n dispatch
kubectl auth can-i list pods --as=system:serviceaccount:dispatch:dispatch-reader -n kube-system
```

Each prints `yes` or `no`.
Your own `kubectl get pods` working proves nothing about the application, because you are a different identity with far more access.

## Test from the Pod itself

The strongest test is a real request using the Pod’s own token.
The `inventory` Deployment in this lab exists for exactly that.
This command runs a small Python script inside it that reads the token and asks the API to list Pods:

```sh
kubectl exec deployment/inventory -- python -c '
import ssl, urllib.request, urllib.error
base = "/var/run/secrets/kubernetes.io/serviceaccount/"
token = open(base + "token").read()
context = ssl.create_default_context(cafile=base + "ca.crt")
for path in ["/api/v1/namespaces/dispatch/pods", "/api/v1/namespaces/dispatch/secrets", "/api/v1/namespaces/kube-system/pods"]:
    request = urllib.request.Request("https://kubernetes.default.svc" + path, headers={"Authorization": "Bearer " + token})
    try:
        print(path, urllib.request.urlopen(request, context=context).status)
    except urllib.error.HTTPError as error:
        print(path, error.code)
'
```

`ca.crt` lets the script check it is really talking to your cluster’s API server.
`200` means allowed.
`403` means the request reached the API, which identified the Pod and then refused it: that is RBAC saying no.
A timeout or connection error would be a network problem, which is a different thing entirely.

After your fix you should see `200` for Pods in `dispatch`, and `403` for both Secrets and `kube-system` Pods.
