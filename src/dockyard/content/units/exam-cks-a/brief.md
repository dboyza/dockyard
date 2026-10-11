# Cluster and system hardening assessment

Eight tasks, each with its weight, on this lab's two-node kubeadm cluster.
Use the existing nodes; do not reset, rejoin, or rebuild them.
`$DOCKYARD_CONTROL_PLANE` and `$DOCKYARD_WORKER` hold the VM names for `limactl shell`; the Kubernetes node names add a `lima-` prefix.
kube-bench is installed on both nodes; use `--benchmark cis-1.12`.

## 1. Fix the worker's kubelet benchmark findings (15%)

kube-bench reports checks 4.2.1 and 4.2.2 as failing on the worker.
Make the worker's kubelet refuse anonymous requests and authorize requests through the API server, and make sure the running kubelet uses the new settings.

## 2. Restrict anonymous access to the API server (10%)

Callers without credentials can read objects in the cluster.

- Remove whatever grants anonymous callers access.
- Configure the API server so requests without credentials are refused with 401, except for `/livez`, `/readyz`, and `/healthz`.

## 3. Trim the CI deployer's access (10%)

ServiceAccount `deployer` in namespace `ci` holds `cluster-admin`.
It needs only to `get`, `list`, `watch`, `patch`, and `update` Deployments in namespace `dispatch`.
Give it exactly that, and remove the cluster-wide grant.

## 4. Confine the document processor with AppArmor (15%)

Deployment `processor` in namespace `processing` runs as root with no AppArmor profile.
The profile `dockyard-processor` is in your workspace.

- Load it in enforce mode on both nodes, so it also survives a reboot.
- Run the processor under it, still as root, and keep it processing documents.

## 5. Encrypt Secrets at rest (15%)

Configure the API server to encrypt Secrets in etcd with `aescbc`, `aesgcm`, or `secretbox`, keeping `identity` last.
Make sure every existing Secret in namespaces `dispatch` and `frontend` is stored encrypted.

## 6. Keep frontend Pods away from node endpoints (10%)

Pods in namespace `frontend` can reach the node metadata address `169.254.169.254` and port 10250 on both nodes.
Allow frontend Pods only DNS and the Dispatch API on port 8080, using `frontend-egress.yaml`.
The trusted client must still submit jobs.

## 7. Verify the staged binaries (10%)

`/opt/dockyard/staged` on the control-plane node holds `kubeadm`, `kubelet`, and `kubectl`.
Official SHA-512 checksums are in your workspace's `release-checksums` folder.
Delete every staged binary that does not match, and keep those that do.

## 8. Turn on audit logging and find a Secret reader (15%)

- Enable API server auditing with a policy that records Secret access at `Metadata` level and never with request or response bodies, with `--audit-log-maxage` and `--audit-log-maxbackup` set.
- Something reads the `dispatch-database` Secret every 20 seconds. Write its full username into `finding.txt` in your workspace.

Throughout, keep the namespace `dispatch`, both Node objects, the `maintenance-sentinel` ConfigMap, and the stored job, and keep Dispatch processing jobs.
