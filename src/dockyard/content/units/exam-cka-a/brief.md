# Native cluster operations assessment

Use the two owned Linux machines and retain their existing identities.
The eight outcomes are separate but storage and transport repairs make the final application transaction possible.

## 1. Capture and inspect a live etcd backup (15%)

Save a new snapshot of the running primary etcd member as `/var/lib/etcd/operations-a.db` inside its mounted data directory.
Use authenticated TLS and verify the snapshot using etcdutl.
Its revision must include the current exam baseline and its key count and integrity hash must be valid.
Do not stop or replace the cluster to satisfy a backup task.

## 2. Provide a limited incident observer (10%)

Grant existing ServiceAccount `incident-observer` in namespace `dispatch` get, list, and watch for Pods and get for Pod logs in that namespace.
It must not read Secrets, create or delete Pods, or update Deployments.
Verify effective authorization, including the denied operations.

## 3. Recover cluster-name resolution for the client (10%)

Restore resolution of `dispatch.dispatch.svc.cluster.local` from Deployment `trusted-client` in namespace `frontend`.
Its DNS policy changed during a maintenance edit.
Use the cluster DNS configuration and retain the original client process.

## 4. Recover the existing database volume placement (15%)

Recover database StatefulSet `db` using its existing claim and the worker-local volume.
Its current node selector names an unavailable node.
The original worker is identified by DOCKYARD_WORKER and has a `dockyard.io/batch=true:NoSchedule` taint that must remain.
Select that worker and add the necessary toleration for the database.
Preserve the original namespace, both Node identities, maintenance sentinel, database claim, and seeded row.

## 5. Run one observation agent on every native node (10%)

Create DaemonSet `node-observer` in namespace `dispatch` with one ready Python process on each of the two native nodes.
Use the supplied application image and a long-running Python process; no privileged host mounts are needed.
Account for node taints through appropriate tolerations.
Do not remove the worker's dedicated taint or change the DaemonSet into a Deployment.

## 6. Place the batch audit on its dedicated worker (10%)

Repair Deployment `batch-audit` so one available replica runs on the original worker.
Use its `dockyard.io/pool=batch` node label and tolerate `dockyard.io/batch=true:NoSchedule`.
Retain that label and taint, and use a node selector rather than hard-coding a Pod nodeName.

## 7. Install the operations report with a Helm override (10%)

Install the supplied `ops-chart` as Helm release `operations-report` in namespace `dispatch`.
Override its environment to `production` while retaining its supplied running HTTP consumer.
Verify the Helm release is deployed and the actual process serves production from `/environment`.

## 8. Recover useful cross-node application traffic (20%)

Repair the worker's disabled IPv4 forwarding without replacing the node or disabling the CNI.
The trusted frontend on the control-plane node must reach the API Service on the worker.
The browser-ready endpoint and a fresh Dispatch job must succeed, including the independently stored worker result.
Keep the existing network policies and original application components.
