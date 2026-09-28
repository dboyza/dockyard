## More than one container in a Pod

A Pod can hold several containers.
They always run on the same node, start and stop together, share one network address, and can share folders.
That tight coupling is useful for small helpers, but wrong for things that should scale separately: Dispatch’s API and workers stay in separate Pods.

Two common helper patterns:

- An **init container** runs to completion *before* the main containers start. It is good for preparation, such as writing a config file or waiting for a dependency.
- A **sidecar** runs *alongside* the main container for the Pod’s whole life, for example to ship logs or watch a file.

## Sharing files with emptyDir

An **emptyDir** volume is an empty folder created when the Pod starts.
Every container that mounts it sees the same files.
It survives a single container restarting, but is deleted when the Pod is deleted, so it is for scratch data, not anything you need to keep.

Each container lists the volumes it uses under `volumeMounts`, by name.
Two containers only share a folder if they mount the *same* volume name.

## This lab

Each worker Pod has three containers:

- `configure`, an init container that should write `queue=redis://queue:6379/0` into `/shared/worker.conf`;
- `worker`, which refuses to start unless that file exists;
- `observer`, a sidecar that prints the file every two seconds.

Right now the init container fails, so the Pod never gets past its init stage.
Look at the evidence:

```sh
kubectl get pods -l app=worker
kubectl describe pod POD_NAME
kubectl logs POD_NAME -c configure
```

A status such as `Init:Error` or `Init:CrashLoopBackOff` means an init container failed.
`-c configure` picks which container’s logs to read, since there is more than one.

There is a second, quieter problem: the `observer` mounts a different emptyDir from the worker, so even when the file exists, the observer cannot see it.

## Check both containers see the same file

After your fix is applied and the Pods are ready:

```sh
kubectl exec deployment/worker -c worker -- cat /shared/worker.conf
kubectl logs deployment/worker -c observer --tail=5
```

`deployment/worker` lets kubectl pick one of the Deployment’s current Pods, which avoids accidentally choosing an old Pod that is still shutting down.
Both commands should show the same `queue=` line.

## Order and sidecars

Kubernetes starts init containers one at a time and only then starts the main containers.
The order of the main containers in the file does not control which starts first.
Newer Kubernetes versions also support **native sidecars**: init containers with `restartPolicy: Always`, which start before the main containers and keep running.
This lab uses the classic style, with the observer listed as a normal container.
