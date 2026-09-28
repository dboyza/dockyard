## Route around the failed control plane

1. Look at HAProxy’s configuration and log on the worker, and at which containers are running on the primary.
2. Generate the correct configuration with `lb-config`, install it on the worker, validate it, and reload HAProxy.
3. Check `kubectl get --raw=/readyz` works again.
4. Choose **Check work**.

Leave the primary’s API server and etcd stopped, and keep all three etcd members in the membership list.
Any configuration that sends traffic to one or both healthy API servers is fine.
In your notes, list the single points of failure that remain.
