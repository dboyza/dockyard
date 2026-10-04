## Upgrading Kubernetes, one step at a time

Upgrading a kubeadm cluster is one of the CKA’s classic tasks.
A cluster has several separately installed pieces, and each must be upgraded on purpose:

- **kubeadm**, the tool that performs the upgrade;
- the **control-plane components**, the API server, controller manager, scheduler, and etcd, which kubeadm upgrades;
- the **kubelet** on every node, a system package;
- **kubectl**, the client.

Installing a newer `kubectl` does not upgrade the cluster, and upgrading kubeadm does not upgrade a running kubelet.
You can only move **one minor version at a time**, for example from 1.36 to 1.37.

This lab starts at Kubernetes 1.36.5 and the target is 1.37.1.

## Look first

Read the official upgrade guide for the target version, then inspect the cluster:

```sh
kubectl get --raw=/version
kubectl get nodes -o wide
kubectl get pods -n kube-system -o wide
kubectl get pdb -A
```

Before a real upgrade, check your add-ons support the new version, look for APIs being removed, and make sure you have a tested etcd backup.

## The order of operations

**On the control-plane node:**

1. Upgrade the kubeadm package.
2. `sudo kubeadm upgrade plan` shows what will change.
3. `sudo kubeadm upgrade apply v1.37.1` upgrades the control-plane components.
4. Drain the node (from your lab terminal), upgrade the kubelet and kubectl packages, then `sudo systemctl daemon-reload` and `sudo systemctl restart kubelet`.
5. Uncordon the node.

**On each worker, one at a time:**

1. Upgrade the kubeadm package, then run `sudo kubeadm upgrade node`. Never `upgrade apply` on a worker.
2. Drain it, upgrade the kubelet and kubectl packages, reload systemd, restart the kubelet.
3. Uncordon it.

```figure
upgrade-order
```

## Packages in this lab

Ubuntu’s package manager usually installs these with `apt-get install kubeadm=1.37.1-1.1`, and they are **held** (`apt-mark hold`) so a routine update never upgrades them by accident.
This lab works offline, so `python -m dockyard.native stage-upgrade` copies the verified package files into each VM at `/tmp/dockyard-$DOCKYARD_LAB-upgrade`; it does not install anything.
`$DOCKYARD_ARCH` holds `arm64` or `amd64` for the file names.

For example, on the control plane:

```sh
packages="/tmp/dockyard-$DOCKYARD_LAB-upgrade"
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo apt-mark unhold kubeadm
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo dpkg -i "$packages/kubeadm_1.37.1-1.1_${DOCKYARD_ARCH}.deb"
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo apt-mark hold kubeadm
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm upgrade plan v1.37.1
```

The kubelet and kubectl packages follow the same unhold, install, hold pattern.
With only one control-plane node, the API is briefly unavailable during the upgrade; this is not a zero-downtime upgrade.

## Wait for each node to really finish

Restarting the kubelet returns immediately, but the node takes a little longer to report its new version and settle.
Before uncordoning a node or moving on, run:

```sh
python -m dockyard.native wait-upgraded-node "$DOCKYARD_CONTROL_PLANE"
python -m dockyard.native wait-upgraded-node "$DOCKYARD_WORKER"
```

It waits until the node reports the new kubelet version and the API stays ready for 30 seconds.

The database’s volume lives on the worker, so draining the worker takes Dispatch’s data offline until the worker returns.
That is planned downtime; the data is safe on the worker’s disk.

## Check the result

When both nodes are Ready and uncordoned, run `python -m dockyard.native refresh-client` and `sh bootstrap.sh` to wait for Dispatch to recover.
Then compare `kubectl get --raw=/version`, the nodes’ kubelet versions, and the control-plane images.
Check work also confirms the cluster is the same one you started with, with the same nodes and data, not a freshly built 1.37 cluster.
