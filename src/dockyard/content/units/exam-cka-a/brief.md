# Native cluster operations assessment

Eight tasks, each with its weight, on this lab's two-node kubeadm cluster.
Use the existing nodes; do not reset, rejoin, or rebuild them.
`$DOCKYARD_CONTROL_PLANE` and `$DOCKYARD_WORKER` hold the VM names for `limactl shell`; the Kubernetes node names add a `lima-` prefix.

## 1. Back up etcd (15%)

On the control-plane node, save a snapshot of the running etcd to `/var/lib/etcd/operations-a.db`.

- Connect with TLS, using etcd's CA, certificate, and key from `/etc/kubernetes/pki/etcd`.
- Check the file with `etcdutl snapshot status`.
- Do not stop etcd or the API server.

## 2. Create a limited observer role (10%)

ServiceAccount `incident-observer` already exists in namespace `dispatch`.
In that namespace, give it:

- `get`, `list`, and `watch` on Pods;
- `get` on Pod logs (`pods/log`).

It must not be able to read Secrets, create or delete Pods, or update Deployments.
Check with `kubectl auth can-i`.

## 3. Fix DNS for the frontend (10%)

Deployment `trusted-client` in namespace `frontend` can no longer resolve `dispatch.dispatch.svc.cluster.local`.
Someone changed its DNS policy.
Make it use the cluster's DNS again, keeping the same container and command.

## 4. Move the database back to its volume (15%)

StatefulSet `db` cannot start: its node selector names a node that does not exist, and its data lives on a local volume on the worker.

- Change the node selector so `db-0` runs on the worker, `lima-$DOCKYARD_WORKER`.
- The worker has the taint `dockyard.io/batch=true:NoSchedule`. Keep the taint, and add a toleration to the database instead.
- Keep the existing claim and volume.

Also keep the namespace, both Node objects, the `maintenance-sentinel` ConfigMap, and the stored job.

## 5. Run an agent on every node (10%)

Create DaemonSet `node-observer` in namespace `dispatch` with one ready Pod on each of the two nodes.

- Use the Dispatch image, `$DOCKYARD_IMAGE` with `imagePullPolicy: Never`, running a long-lived Python process as the container's main process, for example `python -c "import time; time.sleep(86400)"`.
- Add tolerations so it also runs on the control-plane node and the tainted worker. Do not remove any taints.
- Namespace `dispatch` enforces the `restricted` Pod Security level, so the Pod needs a matching security context. Check the DaemonSet's events if no Pods appear.

## 6. Place the batch audit on the batch worker (10%)

Fix Deployment `batch-audit` so it has one available replica on the worker.

- Use a node selector for the worker's label `dockyard.io/pool=batch`, not `nodeName`.
- Tolerate the taint `dockyard.io/batch=true:NoSchedule`.
- Keep the worker's label and taint.

## 7. Install a Helm chart with a value override (10%)

Install the workspace chart `ops-chart` as release `operations-report` in namespace `dispatch`, setting its environment value to `production`.
The release must show as deployed, and the running app must return `production` from `/environment`.

## 8. Restore traffic between the nodes (20%)

IP forwarding has been switched off on the worker, so Pods on the control plane cannot reach Pods on the worker.

- Turn it back on, without replacing the node or removing the network plugin.
- Keep the existing NetworkPolicies and application components.

The frontend on the control-plane node must reach the `dispatch` Service, and a new Dispatch job must complete and be saved.
