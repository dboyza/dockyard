## From prepared machines to a cluster

The two VMs in this lab already have containerd, the kubelet, `kubeadm`, and `kubectl` installed.
They are not a cluster yet.
In this lesson you create the **control plane** on the first machine with `kubeadm init`.

`kubeadm init` does several things in order:

1. **Preflight checks**: is the runtime working, swap off, the required ports free?
2. **Certificates**: it creates a certificate authority (CA) for the cluster and a certificate for each component.
3. **Static Pod manifests**: it writes the API server, controller manager, scheduler, and etcd manifests into `/etc/kubernetes/manifests`, and the kubelet starts them.
4. **Configuration and credentials**: it stores the cluster’s configuration in the API and writes an administrator kubeconfig to `/etc/kubernetes/admin.conf`.

It does **not** install a Pod network, and it does not add other machines.
Those come next lesson.

## The configuration file

kubeadm can take its settings from a YAML file with two documents:

- `InitConfiguration` is about *this* machine: its IP address, the containerd socket, and the kubelet’s node IP.
- `ClusterConfiguration` is about the whole cluster: the Kubernetes version, the stable API address, and the **Pod subnet**, the address range Pods get IPs from.

The Pod subnet here is `10.244.0.0/16`, separate from the VMs’ own `192.168.104.0/24` network.
If the two overlapped, traffic could be routed to the wrong place and fail in confusing ways.

## Worked example

Look at what is installed, then have Dockyard write a configuration for this lab’s machines:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm version -o short
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl info
python -m dockyard.native init-config > init.yaml
cat init.yaml
```

Find the node address, the runtime socket, the API endpoint, the version, and the Pod subnet in `init.yaml`.
The helper only writes the file; kubeadm does the real work.
Send the file into kubeadm inside the VM, then refresh your lab terminal’s client:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm init --config=/dev/stdin < init.yaml
python -m dockyard.native refresh-client
kubectl get nodes
```

`--config=/dev/stdin` with `< init.yaml` passes your local file to kubeadm inside the VM.
`refresh-client` copies the new administrator credentials into your lab’s private kubeconfig; it does not touch `~/.kube/config`.

The node will show **NotReady**, and CoreDNS will be Pending.
That is expected: there is no Pod network yet.

## Preparing a node yourself

In this lab the machines arrive ready, but an exam task may ask you to prepare one.
Kubernetes needs two things from the operating system before `kubeadm init` will pass its checks:

- **IPv4 forwarding** turned on, so the node can pass Pod traffic along. Make it permanent with a file in `/etc/sysctl.d`, then reload the settings:

  ```sh
  echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/k8s.conf
  sudo sysctl --system
  sysctl net.ipv4.ip_forward
  ```

  The last command should print `net.ipv4.ip_forward = 1`.
- A **container runtime** installed and running, such as containerd, or Docker Engine together with **cri-dockerd**, the adapter that lets the kubelet talk to Docker. A runtime supplied as a package file installs with `dpkg` and starts with `systemctl`:

  ```sh
  sudo dpkg -i cri-dockerd_VERSION_amd64.deb
  sudo systemctl enable --now cri-docker.service
  systemctl status cri-docker.service
  ```

If a node has more than one runtime, tell kubeadm which one to use with `--cri-socket`, for example `--cri-socket=unix:///var/run/cri-dockerd.sock`.

## In the exam

You will usually run kubeadm directly on the node with flags instead of a file:

```sh
sudo kubeadm init --kubernetes-version=v1.35.8 --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=NODE_IP
mkdir -p "$HOME/.kube"
sudo cp /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

kubeadm prints these last three lines itself when it finishes, along with a `kubeadm join` command for workers.

## Keep credentials private

The administrator kubeconfig and join tokens give real power over the cluster.
Keep them out of your notes.
