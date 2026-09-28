## Fix crictl on the worker

`crictl` on the worker cannot reach the runtime, although Dispatch is still running.

1. From your lab terminal, run `kubectl get nodes -o wide`.
2. Enter the worker with `limactl shell --workdir=/tmp "$DOCKYARD_WORKER"` and run `sudo crictl info`, `sudo cat /etc/crictl.yaml`, and `systemctl is-active containerd`.
3. Fix `/etc/crictl.yaml` so `sudo crictl info` reaches containerd and reports `RuntimeReady` with the systemd cgroup driver.
4. Find a running Dispatch API container with `crictl`, and show its process is under the systemd cgroup tree.
5. Exit the VM and choose **Check work**.

Dispatch must keep processing new jobs throughout.
In your notes, explain why this fault did not need a rebuilt image or a new node.
