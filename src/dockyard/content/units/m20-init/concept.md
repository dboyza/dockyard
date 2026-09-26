## What kubeadm creates

Prepared Linux guests already contain containerd, kubelet, kubeadm, and kubectl.
They are not yet a Kubernetes cluster.
`kubeadm init` checks prerequisites, creates a certificate authority and component credentials, writes static Pod manifests, and starts the control plane through kubelet.
It also records cluster configuration and bootstrap discovery information in the new API.
It does not install the Pod network implementation or join another machine automatically.

## Read configuration before running it

Kubeadm's `InitConfiguration` describes the first node, including its actual private address, CRI socket, and kubelet node IP.
`ClusterConfiguration` describes shared choices such as the Kubernetes version, stable API endpoint, and Pod subnet.
The two documents serve different scopes even when passed together in one YAML file.
Dockyard's `init-config` helper prints configuration for this attempt's recorded guests; it does not run kubeadm.
The supplied Pod range is `10.244.0.0/16`, separate from the guests' `192.168.104.0/24` network.
Overlapping those networks can produce misleading partial connectivity and routing failures.

## Worked example: inspect the prepared runtime

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm version -o short
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl info
python -m dockyard.native init-config > init.yaml
cat init.yaml
```

Compare the two YAML documents and locate the node address, runtime socket, API endpoint, version, and Pod subnet.
Then pass the reviewed file to the guest's real kubeadm process using standard input:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm init --config=/dev/stdin < init.yaml
python -m dockyard.native refresh-client
kubectl get nodes
```

The refresh helper copies this lab's administrative client into its private host kubeconfig and substitutes the declared loopback endpoint.
It does not change `~/.kube/config`.
The control plane can answer authenticated requests while its node remains NotReady because CNI is still absent.
That is the expected intermediate state for this lesson, not a reason to disable networking checks.

## Credentials are part of the boundary

Administrative kubeconfigs and join tokens grant real privileges inside the practice cluster.
Keep them private and do not paste their contents into notes.
A join token authenticates bootstrap, while the discovery CA hash pins which cluster the worker may trust.
The next lesson uses both to join the worker and install networking.
