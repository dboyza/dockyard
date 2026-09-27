## Give a workload only the permissions it needs

Imagine adding a tool that lists the Pods running Dispatch.
It needs to read Pod information, but it has no reason to read database passwords stored in Secrets.
In this lesson, you’ll remove that unnecessary access while keeping the useful access working.
This is **least privilege**: giving an identity enough permission to do its job, and no more.

Kubernetes makes two separate decisions for each request:

- **Authentication:** who is making this request?
- **Authorization:** is that identity allowed to do this operation?

A **ServiceAccount** gives a workload an identity.
A **Role** lists allowed operations within a namespace.
A **RoleBinding** connects that Role to the identities allowed to use it.
A ServiceAccount alone does not grant permission to read Pods or Secrets.

You met these objects in the earlier identities lesson.
Here you’ll test what the account can actually do, including requests that must fail.

## Understand the practice setup

Open `identity.yaml` in the lab workspace.
It contains the `dispatch-reader` ServiceAccount, the `dispatch-pod-reader` Role and RoleBinding, and an `inventory` Deployment.
The inventory Pod is a practice client: its normal command waits, and the checker runs API requests inside it.
It is not a finished inventory application.

This Pod has a short-lived ServiceAccount token, a credential Kubernetes uses to recognize the requester.
Its mounted CA certificate lets the client verify that it is talking to the cluster’s API server over HTTPS.
The checker uses those files inside the Pod without displaying the token.
Do not copy credentials into notes or Git.

Dispatch’s API and worker do not need to call the Kubernetes API, so their `dispatch-app` account has automatic token mounting disabled.
Their database password serves a different purpose and should stay in place.

## Read a Role rule

For example, a reporting tool that reads ConfigMaps might have this rule:

```yaml
rules:
- apiGroups: [""]
  resources: [configmaps]
  verbs: [get, list]
```

`resources` names the kinds of objects the tool may access.
`verbs` names the allowed operations: `get` reads one named object and `list` reads a collection.
The empty `apiGroups` value means Kubernetes’s core API group, which includes Pods, Secrets, and ConfigMaps.
Deployments belong to the `apps` group instead.

In your task, inspect the rule for the Pod reader.
Keep its Pod reads, but remove access it does not need.
Avoid `*`, which would grant access to every matching resource or operation.
Reading Pods does not automatically grant access to their logs or permission to run commands inside them; those use separate subresources such as `pods/log` and `pods/exec`.

A RoleBinding grants access within its namespace.
A ClusterRole can also supply rules to a RoleBinding without granting access everywhere.
A ClusterRoleBinding, by contrast, grants the referenced permissions across the cluster.
Do not widen this task to cluster-wide access.

## Ask what the account is allowed to do

```sh
kubectl get role dispatch-pod-reader -n dispatch -o yaml
kubectl get rolebinding dispatch-pod-reader -n dispatch -o yaml
kubectl auth can-i list pods -n dispatch --as=system:serviceaccount:dispatch:dispatch-reader
kubectl auth can-i get secrets -n dispatch --as=system:serviceaccount:dispatch:dispatch-reader
kubectl auth can-i list pods -n kube-system --as=system:serviceaccount:dispatch:dispatch-reader
```

`--as` asks the permission question as the practice account.
Your lab administrator account is allowed to do this; it is not permission every Kubernetes user has.
After your repair, the three answers should be `yes`, `no`, and `no`.
Running these checks without `--as` would test your administrator permissions instead.

After editing and saving `identity.yaml`, apply it with:

```sh
python render.py identity.yaml | kubectl apply -f -
```

The supplied renderer replaces placeholders such as the lab image name.
The pipe sends the resulting YAML to `kubectl`; the final `-` tells kubectl to read that input.
Use this command for the edited identity file so unrelated configuration stays as it was.

## Check a real request, too

The checker makes HTTPS requests from the inventory Pod using its actual token.
It expects HTTP **200** for reading Dispatch Pods and **403** for reading Secrets or Pods in `kube-system`.
A 403 means the API understood the identity but refused that operation.
A timeout or certificate error does not establish that permission was denied.
Open **Measured state** in the result to see those status codes.

The checker also verifies that the account cannot create Pods, patch Deployments, or create RoleBindings.
It checks that the API and worker remain token-free and that Dispatch can still complete a job.
Security changes need both kinds of evidence: the forbidden action fails and the useful work still succeeds.
