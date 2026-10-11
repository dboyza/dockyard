## Cut access back to what was agreed

Two subjects hold far more access than `access-requirements.md` says they need: the CI deployer ServiceAccount and the `dispatch-operators` group.

1. Find their cluster-wide bindings, and measure what each can really do with `kubectl auth can-i --list` and `--as`.
2. Write `rbac.yaml` granting each exactly what the requirements describe, scoped to the `dispatch` namespace.
3. Apply it, remove the broad bindings and the wildcard ClusterRole, and choose **Check work**.

Leave the built-in `system:` and `kubeadm:` bindings alone.
In your notes, list one thing each subject could do before your change that it must not do, and how you confirmed it is now refused.
