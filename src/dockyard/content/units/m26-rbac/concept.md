## Access that grew without anyone noticing

RBAC permissions tend to grow.
A pipeline fails, someone grants `cluster-admin` "for now", and it stays.
A team asks for access, someone writes a role with `*` everywhere, and nobody revisits it.
Each grant looked harmless when it was made; together they mean a stolen CI token or one compromised laptop controls the whole cluster.

This lesson is about finding that kind of access and cutting it back to what each team agreed it needs, written down in `access-requirements.md`.

## Reading who has what

Remember the four RBAC objects:

- A **Role** lists permissions inside one namespace; a **ClusterRole** lists permissions that can apply everywhere.
- A **RoleBinding** grants a role to subjects inside one namespace; a **ClusterRoleBinding** grants a ClusterRole across the whole cluster.

Subjects are users, groups, or ServiceAccounts.
Start with the cluster-wide grants, because they are the widest:

```sh
kubectl get clusterrolebindings -o wide
```

The `ROLE` column shows the role and the `USERS`, `GROUPS`, and `SERVICEACCOUNTS` columns show who holds it.
Most entries are defaults whose names start with `system:`, `kubeadm:`, or `calico`; look hard at the rest.
To see what a role actually allows, describe it:

```sh
kubectl describe clusterrole dispatch-ops
```

```figure
rbac-audit
```

## Asking the API server as someone else

Reading roles is error-prone, because permissions add up across bindings.
The reliable check is to ask the API server what a subject can do, with **impersonation** through `--as` and `--as-group`:

```sh
kubectl auth can-i --list --as=system:serviceaccount:ci:deployer
kubectl auth can-i get secrets -n dispatch --as=alex --as-group=dispatch-operators
```

The first lists everything the CI deployer may do; a line with `*.*` and `[*]` means everything.
The second answers `yes` or `no` for one action.
A ServiceAccount's username is always `system:serviceaccount:NAMESPACE:NAME`.
For a group, any made-up user name works, because the check is about the group.

Some permissions deserve extra suspicion even when they look narrow: anything on `secrets`, `pods/exec`, `nodes/proxy`, and the verbs `escalate`, `bind`, and `impersonate`, each of which can be turned into more access.

## Narrowing the scope

There are two levers: what a role allows, and where it is granted.

```figure
rbac-scope
```

A RoleBinding in `dispatch` can refer to a ClusterRole.
The ClusterRole's permissions then apply only inside `dispatch`.
That makes the built-in `view` ClusterRole, which reads almost everything but deliberately excludes Secrets, a ready-made answer for read-only access to one namespace.
For the deployer, write a small Role with only the Deployment verbs it needs.

## Fix it

1. Find the two cluster-wide bindings that give the CI deployer and the operators far more than `access-requirements.md` allows.
2. Write `rbac.yaml` with a Role and RoleBinding for the deployer in `dispatch`, and a RoleBinding of the `view` ClusterRole for the `dispatch-operators` group in `dispatch`.
3. Apply it, then delete the two broad ClusterRoleBindings and the `dispatch-ops` ClusterRole.
4. Check each requirement with `kubectl auth can-i`, including the things each subject must **not** be able to do.

## If something goes wrong

- **A subject still can do too much**: another binding still grants it. Search all bindings with `kubectl get clusterrolebindings,rolebindings -A -o wide | grep -E 'deployer|dispatch-operators'`.
- **The deployer cannot patch Deployments**: Deployments are in the `apps` API group, so the Role's `apiGroups` must be `["apps"]`, not `[""]`.
- **`can-i` for the group says no to everything**: check the RoleBinding's subject has `kind: Group` and `apiGroup: rbac.authorization.k8s.io`.
