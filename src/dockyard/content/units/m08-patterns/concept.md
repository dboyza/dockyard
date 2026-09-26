# Share a lifecycle only when it helps

Containers in one Pod share a network namespace and can mount the same volume.
They are scheduled together and generally replaced together.
Use this coupling deliberately: an API and a separately scalable worker belong in separate Pods, while a helper that prepares or observes one worker's local files can share its Pod.

An ordinary init container must finish successfully before application containers start.
A failing init container keeps the Pod in an init state; a healthy image in the main container cannot bypass that dependency.
An `emptyDir` volume starts empty with the Pod and survives individual container restarts, but deleting the Pod deletes its contents.
This makes it suitable for generated scratch configuration, not durable business data.

## Worked example

```sh
kubectl describe pod POD_NAME
kubectl logs POD_NAME -c configure
kubectl logs POD_NAME -c observer --tail=10
kubectl exec POD_NAME -c worker -- cat /shared/worker.conf
```

The supplied init container writes `queue=redis://queue:6379/0` to a shared file.
The worker refuses to start without that file, and the observer sidecar prints it periodically.
The exercise uses a regular long-running sidecar; Kubernetes also supports native sidecars as init containers with `restartPolicy: Always`, which have distinct startup and termination semantics.
Do not assume regular container list order provides startup ordering.

For an alternative valid implementation, generate the same configuration with a different finite init command and keep both required consumers mounted to the same Pod-scoped volume.
