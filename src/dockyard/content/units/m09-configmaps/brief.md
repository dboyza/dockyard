## Make Dispatch use its ConfigMap

The `dispatch-settings` ConfigMap holds `environment: learning` and the correct banner, but the API is not using either.

1. Compare the ConfigMap with how the Deployment in `platform.yaml` sets `DISPATCH_ENV` and mounts `/config`.
2. Make `DISPATCH_ENV` come from the ConfigMap’s `environment` key using `configMapKeyRef`.
3. Make `/config/banner.txt` contain the ConfigMap’s `banner.txt` value, `Configured through the Kubernetes API.`
4. Run `sh run.sh`, wait for the rollout, and check `/config` through the Service.
5. Choose **Check work**.

Optional experiment: change the banner in the ConfigMap with `kubectl edit configmap dispatch-settings`, then request `/config` every few seconds, for up to two minutes, until it changes.
Do not restart anything.
Put the original banner back before checking.
Think about why the same experiment would not work for `DISPATCH_ENV`.
