## Shrink the worker's footprint

The worker runs more than a Kubernetes node needs.

1. Survey its running services and listening ports, and find the service that serves files to the whole network.
2. Stop that service, stop it starting again, and confirm its port is closed.
3. Find the account that can use `sudo` without a password, and retire it so it can neither log in nor use `sudo`.
4. Choose **Check work**.

Do not touch the kubelet, containerd, or SSH, and keep Dispatch processing jobs.
In your notes, explain the difference between stopping, disabling, and masking a service.
