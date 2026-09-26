## A cluster has several independently installed versions

This fixture starts with a real Kubernetes 1.34.12 control plane and kubelets.
The target is the frozen 1.35.8 course version.
Installing a newer host `kubectl` does not upgrade the server, and replacing only `kubeadm` does not upgrade a running kubelet.
The outcome must be visible in the API version, component images, and every node's reported kubelet version.
The supported path advances one minor version at a time.

Read the linked version-specific upgrade guide and inspect this cluster before changing it:

```sh
kubectl get --raw=/version
kubectl get nodes -o wide
kubectl get pods -n kube-system -o wide
kubectl get pdb -A
```

Check add-on compatibility, removed APIs, backup readiness, and workload maintenance requirements before a production upgrade.
The pinned Calico release supports both course versions.
This fixture uses currently served APIs, but that does not prove an arbitrary application has no deprecated API clients.
Use API discovery and workload/controller inventories alongside release deprecation guidance.

## Stage packages without installing them

`python -m dockyard.native stage-upgrade` transfers verified Debian archives into each recorded guest.
It does not execute the upgrade.
The directory is `/tmp/dockyard-$DOCKYARD_LAB-upgrade` inside each guest.
Use the actual package names `kubeadm_1.35.8-1.1_arm64.deb`, `kubelet_1.35.8-1.1_arm64.deb`, and `kubectl_1.35.8-1.1_arm64.deb`.
Temporary unhold/install/hold steps make the version choice explicit:

```sh
packages="/tmp/dockyard-$DOCKYARD_LAB-upgrade"
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo apt-mark unhold kubeadm
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo dpkg -i "$packages/kubeadm_1.35.8-1.1_arm64.deb"
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo apt-mark hold kubeadm
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm upgrade plan v1.35.8
```

Review the plan before running `sudo kubeadm upgrade apply v1.35.8` inside the control-plane guest.
Kubeadm updates static component manifests and associated cluster configuration.
This single-control-plane lab has a deliberate API maintenance interruption; it is not a zero-downtime upgrade demonstration.

## Upgrade one node at a time

After the control-plane upgrade, drain that node through the private host client before replacing its kubelet and kubectl packages.
Use `--ignore-daemonsets --delete-emptydir-data` only after identifying the fixture's disposable scratch volumes.
Run `systemctl daemon-reload` and restart kubelet.
Before uncordoning or touching the next node, use `python -m dockyard.native wait-upgraded-node "$DOCKYARD_CONTROL_PLANE"` for the primary, or the same helper with `$DOCKYARD_WORKER` for the worker.
This observation waits for the reported target kubelet version and API readiness to remain stable for 30 seconds, including unchanged running static component identities on the primary.
A service restart returning successfully is not proof that its asynchronous reconciliation has finished.
Then uncordon the node.
On the worker, first install the target kubeadm package and run `sudo kubeadm upgrade node` before its drain and kubelet package update.
Do not run `upgrade apply` on the worker.
Restore package holds after each explicit installation.

The database uses a retained worker-local PV, so draining that worker also creates planned application downtime.
Its data remains on that worker and becomes usable again when it returns.
The earlier drain lesson demonstrated moving stateless replicas to spare capacity; it did not make this local disk portable.

## Verify continuity, not just a version string

Wait for both nodes to become Ready and schedulable, refresh the private client, and use `sh bootstrap.sh` to wait for the existing Dispatch checkpoint to recover.
Compare `kubectl get --raw=/version`, node kubelet versions, and control-plane images.
The assessment requires the original namespace, Node UIDs, ConfigMap identity, and a pre-maintenance SQL row to remain intact, then submits fresh work.
Resetting into a brand-new 1.35 cluster is useful for a different task but does not satisfy an in-place upgrade.
