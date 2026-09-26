## Three voters tolerate one unavailable member

This lab has three control-plane guests, each with an API server and a stacked etcd member, plus one worker.
Etcd commits changes through a majority of its voting members.
Three voters require two acknowledgments, so one unavailable member can be tolerated; losing two removes the majority.
Do not remove members just to make a health report look smaller.
The assessment confirms that the original three voting identities remain in membership and both surviving endpoints are healthy.

## An endpoint must reach surviving servers

Clients use one stable endpoint on the worker's HAProxy listener.
HAProxy forwards TCP to the API servers, which terminate TLS using certificates valid for the endpoint.
Health checks remove unreachable backends from selection.
An etcd majority cannot help a client whose only configured load balancer backend is the unavailable API server.
Likewise, a TCP listener alone does not prove the API can commit data.

## The actual failure in this lab

The primary guest's API-server and etcd static manifests have been moved outside kubelet's manifest directory.
Both corresponding containers are stopped; the VM and kubelet remain running.
The other two control-plane guests retain quorum.
The load balancer currently selects only the failed primary, so the private client cannot reach a healthy API server.
Keep the primary outage in place while repairing the load balancer.
The fixture spreads three DNS replicas across the control planes and places its diagnostic frontend on a surviving node.
This matters because kubeadm control-plane kubelets use their local API endpoint, so remote Pod operations on the failed primary can lose authorization even while another API server remains healthy.
The failed node can become NotReady; surviving DNS and application dependencies must remain available independently.

## Worked example: inspect the endpoint before changing it

```sh
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo cat /etc/haproxy/haproxy.cfg
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo journalctl -u haproxy -n 20 --no-pager
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl ps
python -m dockyard.native lb-config > haproxy.cfg
cat haproxy.cfg
```

The helper prints the recorded topology as a normal HAProxy configuration; it does not apply it.
A backend line names a private control-plane endpoint and enables TCP health checks.
Install the reviewed configuration, validate syntax with `haproxy -c -f /etc/haproxy/haproxy.cfg`, and reload the service.
Use `sudo tee /etc/haproxy/haproxy.cfg < haproxy.cfg` through `limactl shell` to transfer it without a host mount.

## Prove a write, then state the limits

`kubectl get --raw=/readyz` checks API readiness.
The assessment also creates a uniquely named ConfigMap through the private endpoint, reads its value, and deletes it.
It checks the surviving etcd endpoints directly through their runtime containers, and completes a new Dispatch job.
Those observations establish useful control-plane operation during this one-member outage.
They do not establish whole-system high availability: the worker-hosted load balancer, local database volume, Mac, and VM host are still single failure points.
Production endpoint and storage redundancy require separate designs.
