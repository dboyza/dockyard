Recover kubelet supervision on the worker without replacing the VM or rebuilding Dispatch.
Both guests must have active kubelet services, fresh node leases, and Ready conditions.
A new Dispatch job must complete through the existing application.

Inspect the worker before changing it:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_WORKER"
systemctl status kubelet --no-pager
sudo journalctl -u kubelet -n 30 --no-pager
systemctl cat kubelet
```

Use the observations to decide whether the service needs a start or a configuration repair.
After the repair, return to the host shell and compare node conditions with lease renewal times.
Record why an existing container can remain alive while its node loses active supervision.
