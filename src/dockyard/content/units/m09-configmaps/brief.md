# Connect intent to the running process

The ConfigMap contains `environment: learning` and the expected banner, but the API uses a literal stale environment value and mounts the wrong banner key.

1. Inspect the ConfigMap and the Deployment references separately.
2. Select the ConfigMap's `environment` key as `DISPATCH_ENV` with `configMapKeyRef`.
3. Mount the ConfigMap so `/config/banner.txt` contains `Configured through the Kubernetes API.`.
4. Apply your changes and wait for the API rollout.
5. Query `/config` through the Service to observe both delivery paths.

As a follow-up experiment, edit the banner in the ConfigMap and watch for the projected file update without restarting.
Restore the required banner before checking.
Do the same thought experiment for the environment key and explain why it needs replacement instead.
