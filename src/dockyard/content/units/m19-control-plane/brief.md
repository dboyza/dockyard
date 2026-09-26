Repair the separate control-plane guest client at `$HOME/.kube/operator.conf`.
It must authenticate to the actual native cluster, list both nodes, and remain private with mode 600.
All four control-plane static components must be running, the API serving certificate must validate against its CA, and Dispatch must process a new job.

Compare the host and guest observations:

```sh
kubectl get nodes
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"
kubectl --kubeconfig="$HOME/.kube/operator.conf" --request-timeout=5s get nodes
sudo crictl ps
```

Inspect the selected endpoint without printing credentials:

```sh
kubectl --kubeconfig="$HOME/.kube/operator.conf" config view -o jsonpath='{.clusters[0].cluster.server}'
```

Use the error category and the control-plane evidence to repair the guest client.
Do not turn off certificate verification, change the Mac's default kubeconfig, or replace healthy static components.
Explain why the host could still reach the cluster while the separate guest client failed.
