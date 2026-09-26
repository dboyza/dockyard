Repair runtime inspection on the worker while preserving Dispatch.
`sudo crictl info` must reach the actual runtime through the guest's normal `/etc/crictl.yaml`, report RuntimeReady, and use systemd cgroups.
Find a running API container through CRI and inspect its Linux process membership.
The completed application must still accept and process a fresh job.

Start with these observations from the host workspace:

```sh
kubectl get nodes -o wide
limactl shell --workdir=/tmp "$DOCKYARD_WORKER"
sudo crictl info
sudo cat /etc/crictl.yaml
systemctl is-active containerd
```

Compare the configured endpoint with the runtime socket taught in the worked example.
Repair the client configuration in the worker guest, then repeat your observations.
Explain in your notes why this fault did not require rebuilding the Dispatch image or replacing the node.
