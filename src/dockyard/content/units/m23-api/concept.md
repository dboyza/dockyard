## When kubectl cannot help

kubectl does almost everything by talking to the API server.
If the API server itself is broken, kubectl can only tell you it cannot connect, and running it again and again teaches you nothing new.
You need to go below the API, to the control-plane node, and use tools that do not depend on it: `systemctl`, `journalctl`, `crictl`, and the static Pod manifests.

The API server depends on etcd.
It finds etcd through its `--etcd-servers` flag, and connects using certificates given by `--etcd-cafile`, `--etcd-certfile`, and `--etcd-keyfile`.
If any of those are wrong, the API server starts, fails to reach its database, and exits, over and over.

In this lab someone changed the API server's etcd address.
etcd itself is still running normally.

## Read the error message carefully

Different problems produce different errors, and each points to a different fix:

| Error contains | Likely meaning |
| --- | --- |
| `connection refused` | Nothing is listening at that address and port: a wrong address, or the service is down. |
| `certificate signed by unknown authority`, `x509` | The TLS certificates do not match: a wrong CA or certificate path. |
| `Unauthorized`, `Forbidden` | The connection works, but the credentials or permissions are wrong. |
| `no such host` | A name that does not resolve. |

Fix what the evidence points to.
Never switch off certificate checking or rebuild the cluster to get past an error like these.

## Worked example: follow the failure

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl ps -a --name kube-apiserver
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl ps --name etcd
```

`crictl ps -a` includes stopped containers, so you can see the API server's recent failed attempts.
Read the log of the most recent one:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl logs --tail=30 CONTAINER_ID
```

The newest container is listed first.
Its log lines are long; the useful part is at the end, for example `dial tcp 127.0.0.1:PORT: connect: connection refused`.
If the newest log only shows `Shutting down` messages, the kubelet is still replacing the old API server; wait a minute and look again.
Then compare the two sides:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo grep etcd-servers /etc/kubernetes/manifests/kube-apiserver.yaml
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo grep listen-client-urls /etc/kubernetes/manifests/etcd.yaml
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo ss -lntp
```

The first shows where the API server is looking; the second shows where etcd listens; `ss -lntp` lists the ports really open on the node.
If `crictl` shows no API server container at all, check the kubelet's log with `journalctl -u kubelet` instead; a manifest with a YAML mistake is rejected before any container starts.

## Repair

Edit `/etc/kubernetes/manifests/kube-apiserver.yaml` so `--etcd-servers` points at the port etcd really uses, `https://127.0.0.1:2379`.
Change nothing else; the certificate flags are correct.
If you edit a copy first, keep it outside the manifests directory and then move it into place.

The kubelet sees the changed file and starts a new API server container.
Give it a minute before deciding whether the fix worked.

## Check it properly

- `kubectl get --raw=/readyz` shows the API server says it is ready.
- A new Pod getting a node shows the scheduler and API are working together; `python wait-control-plane.py` waits for exactly that.
- A new Dispatch job completing shows the application works end to end.

Check work looks at all of these, and also checks the original nodes, namespace, and database row are still the same ones, so a rebuilt cluster would not pass.
