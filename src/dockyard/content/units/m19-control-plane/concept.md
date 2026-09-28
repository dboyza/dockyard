## When kubectl cannot reach the cluster

When a `kubectl` command fails, the error tells you how far it got.
Learn to read these, because each needs a different fix:

- **connection refused**: nothing is listening at that address and port. Wrong address, or the API server is down.
- **certificate error** (such as “x509: certificate signed by unknown authority”): the client reached the server but cannot trust its certificate.
- **401 Unauthorized**: the server does not accept the client’s credentials.
- **403 Forbidden**: the credentials are accepted, but that user is not allowed to do this.

Never “fix” a certificate error by turning off verification; that hides the problem and removes the protection.

A **kubeconfig** file holds everything a client needs: the server’s address, the certificate authority (CA) to trust, and the user’s credentials.
Because it can contain a private key, keep it readable only by its owner (`chmod 600`).

## The control plane is made of Pods

kubeadm runs the control-plane components, the API server, controller manager, scheduler, and etcd, as **static Pods**.
Their manifests are plain files in `/etc/kubernetes/manifests` on the control-plane node, and the kubelet runs whatever it finds there.
They also appear in `kubectl get pods -n kube-system`, but deleting them there does not remove them; the kubelet recreates them from the files.
If `kubectl` itself is broken, `sudo crictl ps` on the node still shows whether they are running.

## Worked example: check the API server’s certificate

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"
sudo kubeadm certs check-expiration
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -subject -issuer -dates
sudo openssl verify -CAfile /etc/kubernetes/pki/ca.crt /etc/kubernetes/pki/apiserver.crt
sudo crictl ps
exit
```

- `kubeadm certs check-expiration` lists every control-plane certificate and when it expires.
- `openssl x509 ... -dates` shows who the certificate is for, who signed it, and its validity dates.
- `openssl verify` checks it was signed by the cluster’s CA.

Never print private keys (`*.key` files) into your notes.
Renewing certificates comes in the maintenance module; this lesson does not need it.

## Two separate clients

Your lab terminal uses Dockyard’s own kubeconfig, which reaches the cluster through a forwarded port on your computer.
This lab also gives the control-plane VM a separate client file, `$HOME/.kube/operator.conf`, which talks to the API server directly inside the VM network.
That is the one that is broken, and the only one you should change.
kubeadm’s own `/etc/kubernetes/admin.conf` on the control plane is a working administrator kubeconfig you can compare with; it must stay readable only by root.

You can edit a kubeconfig with any text editor, or with kubectl itself:

```sh
kubectl --kubeconfig=FILE config view --minify
kubectl --kubeconfig=FILE config set-cluster CLUSTER_NAME --server=https://HOST:6443
```

`config view` hides embedded keys unless you add `--raw`, so it is safe to read on screen.
The API server normally listens on port 6443.

## Working in this lab’s machines

From this module on, Dispatch runs on two real Ubuntu virtual machines, a control-plane node and a worker node, built with **kubeadm** and **containerd** instead of kind.
This is how most self-managed clusters are built, and it is what the CKA exam uses.

- Your lab terminal still has `kubectl`, already connected to this cluster.
- `limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"` or `"$DOCKYARD_WORKER"` opens a shell *inside* a VM. Type `exit` to come back.
- Inside a VM, `sudo` gives you root on that VM only. Your lab terminal itself still runs with your normal permissions on your computer.
- The database keeps its data on a local volume on the worker, so it is tied to that one machine and not replicated.

Use the VM names in those two variables; do not point commands at other VMs.
