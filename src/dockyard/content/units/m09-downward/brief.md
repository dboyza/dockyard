## Make every Dispatch Pod report where it runs

Both API replicas claim to be a Pod named `dispatch`, so nobody can tell which one served a request.

1. Ask a Pod what `/whereami` reports, and compare it with `kubectl get pods -o wide`.
2. In `platform.yaml`, give the API container its Pod name, namespace, and node through `fieldRef`, and its memory limit through `resourceFieldRef`.
3. Add a `downwardAPI` volume that provides the Pod's labels as `/etc/podinfo/labels`.
4. Run `sh run.sh`, check each Pod's answer against its own Pod, and choose **Check work**.

Keep the existing environment variables, mounts, and resource limits as they are.
In your notes, explain why the labels arrive as a file while the Pod name arrives as an environment variable.
