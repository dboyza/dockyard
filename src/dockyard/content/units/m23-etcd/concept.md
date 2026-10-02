## What etcd holds, and what it does not

**etcd** is the database behind the Kubernetes API.
Every object you have created, every Deployment, Service, ConfigMap, and Secret, is stored there.
If etcd's data is lost, the cluster forgets everything it was told to run.
Backing it up and restoring it is a core CKA task.

An etcd backup is called a **snapshot**: a single file holding the whole database at one moment.
It is important to be clear about what a snapshot does *not* hold.
Dispatch's jobs live in PostgreSQL, on a volume on the worker.
An etcd snapshot remembers that the database's StatefulSet and claim exist, but not the rows inside the database.
Application data needs its own backups, like the ones you practised in module 11.

```figure
etcd-scope
```

## Identity: why "the same name" is not enough

Every Kubernetes object gets a **UID**, a unique ID assigned when it is created.
If you delete a ConfigMap and create a new one with the same name and contents, it gets a new UID: it is a different object that looks the same.
A real restore brings back the original object, with its original UID.

In this lab you will take a snapshot, then delete an original ConfigMap called `maintenance-sentinel`, and bring it back from the snapshot.
Recreating it by hand would give it a new UID and would not pass.

```figure
etcd-restore
```

## Worked example: find etcd on the node

etcd runs as a static Pod on the control-plane node.
Open a shell there and look at it:

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"
sudo crictl ps --name '^etcd$'
sudo cat /etc/kubernetes/manifests/etcd.yaml
```

The manifest shows the settings you will need:

- `--name`, the member's name, which is the node's hostname;
- `--initial-advertise-peer-urls`, the address other members would use to reach it;
- `--cert-file`, `--key-file`, and `--trusted-ca-file`, the certificates it uses;
- the `hostPath` volume that puts the node's `/var/lib/etcd` directory inside the container.

## Take a snapshot

`etcdctl` is etcd's command-line client.
etcd only accepts clients that present a trusted certificate, so every command needs the CA and a client certificate and key.
On an exam machine `etcdctl` is often installed on the node itself.
In this lab it is inside the etcd container, so you run it with `crictl exec`, still inside the control-plane VM:

```sh
sudo crictl exec ETCD_CONTAINER_ID etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/lib/etcd/dockyard-recovery.db
```

Older guides put `ETCDCTL_API=3` in front of `etcdctl`; it selects the current version of the client's commands, which is already the default in current etcd releases.
Because `/var/lib/etcd` is mounted from the node, the snapshot file ends up on the node's disk.

Next, check the file with `etcdutl`, a tool that works on etcd files directly rather than talking to a running server:

```sh
sudo crictl exec ETCD_CONTAINER_ID etcdutl snapshot status /var/lib/etcd/dockyard-recovery.db -w table
```

It shows the snapshot's **revision**, a counter that etcd increases with every change, and how many keys it holds.
The snapshot contains Secrets and credentials, so keep it inside the VM and never copy it into your notes.

## Lose something

Leave the VM and, in the lab terminal, run:

```sh
python -m dockyard.fixtures.recovery stage-loss
kubectl get configmap maintenance-sentinel -n default
```

The helper checks that your snapshot is readable, records its revision, and deletes the original `maintenance-sentinel`.
The `get` now reports it is not found.

## Restore into a new directory

Restoring never overwrites the directory etcd is using.
Instead, `etcdutl snapshot restore` writes a complete new data directory from the snapshot, and you then point etcd at it.
Back inside the control-plane VM:

```sh
sudo crictl exec ETCD_CONTAINER_ID etcdutl snapshot restore /var/lib/etcd/dockyard-recovery.db \
  --data-dir=/var/lib/etcd/dockyard-restored \
  --name=MEMBER_NAME \
  --initial-cluster=MEMBER_NAME=PEER_URL \
  --initial-advertise-peer-urls=PEER_URL \
  --bump-revision=1000000000 --mark-compacted
```

Replace `MEMBER_NAME` and `PEER_URL` with the `--name` and `--initial-advertise-peer-urls` values from the manifest, so the restored member matches the running configuration.
Older guides use `etcdctl snapshot restore`; current etcd moved that job to `etcdutl`.

The last two flags matter for Kubernetes.
Restoring rewinds etcd's revision counter to the snapshot's.
Controllers remember the last revision they saw, and a rewound counter could make them trust out-of-date information.
`--bump-revision` moves the counter far ahead of anything they saw, and `--mark-compacted` tells them the old history is gone, so they re-read everything from scratch.
The size of the bump here is chosen for this small lab, not a production rule.

## Point etcd at the restored data

Copy the manifest somewhere outside the manifests directory first, such as `/var/lib/dockyard/etcd-before-restore.yaml`.
Then edit `/etc/kubernetes/manifests/etcd.yaml` and change only the `hostPath` of the data volume:

```yaml
  - hostPath:
      path: /var/lib/etcd/dockyard-restored
      type: DirectoryOrCreate
    name: etcd-data
```

Leave the container's `mountPath` and its `--data-dir` flag unchanged: the container still sees its data at the same place, but it is now the restored directory.
The kubelet notices the changed manifest and restarts etcd, and the API is unavailable for a short while.
Never keep a backup copy of a manifest in `/etc/kubernetes/manifests`; the kubelet would try to run it too.

## Check that it really recovered

Back in the lab terminal, run `python wait-control-plane.py`.
It retries until the API answers a read and a write and the scheduler places a fresh test Pod, then removes that Pod; its source is in the workspace if you want to see exactly what it does.
Then:

```sh
kubectl get configmap maintenance-sentinel -n default -o jsonpath='{.metadata.uid}'
kubectl get nodes
```

Restored objects briefly show the status they had in the snapshot, so give controllers a minute to catch up before trusting what `kubectl get` reports.

Check work compares the sentinel's UID with the original, checks etcd's revision jumped ahead and the old revision is compacted, schedules a new Pod, and sends a new Dispatch job.
It also checks the database row written before the snapshot is still there, which shows the application data was never part of this restore.
