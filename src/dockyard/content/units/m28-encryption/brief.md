## Encrypt Secrets in etcd

This cluster stores every Secret in etcd as plain data.

1. Confirm it by reading the start of `dispatch-database`'s stored value with `etcdctl`.
2. Create an encryption configuration on the control plane with a new `aescbc` key, keeping `identity` as the last provider.
3. Pass it to the API server and mount it into the static Pod, then wait for the API to return.
4. Rewrite every Secret so it is stored encrypted, confirm the stored value now starts with `k8s:enc:aescbc:v1:`, and choose **Check work**.

Never print or copy the key into your workspace or your notes.
In your notes, explain why existing Secrets stayed plain until you rewrote them, and what would break if `identity` were removed too early.
