## Discovery, credentials, and node registration

A worker does not become a cluster member merely because kubelet is running.
`kubeadm join` discovers the API endpoint, verifies its CA, uses a short-lived bootstrap token, and configures the node's kubelet credentials.
The token is a secret; the CA hash establishes which cluster the worker intends to trust.
Skipping CA verification changes that trust boundary and is not a repair for a wrong endpoint.
This lesson begins with one initialized control plane and an unjoined worker.

## Worked example: inspect the incomplete topology

```sh
kubectl get nodes -o wide
kubectl get pods -n kube-system -o wide
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" systemctl status kubelet --no-pager
```

Only the primary should appear in the API before the join.
Its control-plane services can be healthy while DNS Pods await networking.
Generate a private, attempt-specific join configuration and give it to the worker:

```sh
umask 077
python -m dockyard.native join-config "$DOCKYARD_WORKER" > join.yaml
limactl shell --workdir=/tmp "$DOCKYARD_WORKER" sudo kubeadm join --config=/dev/stdin < join.yaml
rm join.yaml
```

The helper creates credentials and prints configuration; the real guest kubeadm command performs the join.
Removing the temporary file limits accidental exposure but does not revoke the token before its expiry.

## Install the network implementation

The supplied manifest is pinned Calico configured for VXLAN and `10.244.0.0/16` Pod addresses.
VXLAN carries Pod traffic between the private guest node addresses.
Each node needs a functioning CNI agent, while CoreDNS needs running Pods and Service connectivity.
Inspect the rendered manifest, then apply it:

```sh
python -m dockyard.native network-manifest > calico.yaml
kubectl apply -f calico.yaml
kubectl wait --for=condition=Ready nodes --all --timeout=240s
kubectl rollout status daemonset/calico-node -n kube-system --timeout=240s
kubectl rollout status deployment/coredns -n kube-system --timeout=240s
sh bootstrap.sh
```

The last script deploys the supplied hardened Dispatch checkpoint and its worker-local persistent storage.
Its frontend client runs on the control-plane guest and reaches the API on the worker by a Kubernetes Service DNS name.
A new job must travel through that path, the queue, a worker process, and the database.
This observed transaction complements node conditions; a Ready label alone is not networking proof.
