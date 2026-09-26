# An image and its configuration have different lifecycles

An image contains the application artifact; a ConfigMap stores non-confidential configuration for one namespace.
A Pod can select a key as an environment variable, import a set of keys, or mount keys as files.
The object existing in the API does not mean that a running process actually consumes it.

Environment values are selected when a container starts.
Editing a ConfigMap does not rewrite an existing process environment, so a controlled replacement is required to consume changed environment values.
Ordinary ConfigMap volume projections are updated eventually, but the application must reread the file to observe the update.
A `subPath` mount does not receive those projected updates.
Dispatch's `/config` endpoint rereads its mounted banner file on every request and reports the environment selected at process startup.

## Worked example

```sh
kubectl get configmap dispatch-settings -o yaml
kubectl describe deployment dispatch
kubectl exec deployment/dispatch -c api -- cat /config/banner.txt
kubectl rollout restart deployment/dispatch
kubectl rollout status deployment/dispatch --timeout=90s
```

A rollout restart changes the Pod template so the controller replaces Pods.
It is different from rebuilding the application image and from editing a single running container.
Service-generated environment variables are disabled in this checkpoint because implicit variables such as `DB_PORT` can collide with an application's explicit configuration.
DNS-based service discovery still works.
