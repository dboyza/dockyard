## What changed

The CI deployer can now read and update Deployments in `dispatch` and nothing else, so a stolen CI token no longer controls the cluster.
The operators can read `dispatch`, including logs, through the built-in `view` role, without seeing Secrets or changing anything.
Both grants are RoleBindings, so they stop at the namespace boundary.

Check your understanding: why is a RoleBinding to the `view` ClusterRole safer than a ClusterRoleBinding to it, even though the role is the same?
Why is `kubectl auth can-i` a better check than reading the roles yourself?
