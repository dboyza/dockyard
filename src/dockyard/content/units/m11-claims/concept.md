## Give the database storage that outlives its Pod

Until now, Dispatch’s database has kept its data in an `emptyDir`, which is deleted with the Pod.
In this lesson you’ll connect it to **persistent storage** and prove the data survives the Pod being replaced.

## Three objects, one chain

Kubernetes separates *asking for* storage from *providing* it:

- A **PersistentVolumeClaim (PVC)** is a request: “I need 1 GiB that one node can read and write.” It lives in your namespace.
- A **PersistentVolume (PV)** is a real piece of storage that can satisfy one claim. It belongs to the whole cluster.
- A **StorageClass** describes a kind of storage and how to create PVs of that kind automatically.

When a claim names a StorageClass, the class’s **provisioner** creates a matching PV for it.
This is **dynamic provisioning**.
The claim and PV are then **Bound** to each other.

The chain from database to disk looks like this:

```text
PostgreSQL writes /var/lib/postgresql/data
  -> volumeMounts entry in the container
  -> volumes entry in the Pod, pointing at a claim
  -> PersistentVolumeClaim dispatch-data
  -> PersistentVolume (created for the claim)
  -> real storage on the node
```

A claim that exists but is not referenced by the Pod does nothing for your data.

The model below lets you remove each link in that chain and see which lifetime ends with it.

```figure
storage-model
```

## A claim in YAML

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dispatch-data
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard
  resources:
    requests:
      storage: 1Gi
```

And the Pod side, replacing an `emptyDir`:

```yaml
volumes:
- name: data
  persistentVolumeClaim:
    claimName: dispatch-data
```

## Access modes

- **ReadWriteOnce (RWO)**: mounted read-write by one *node* at a time. Several Pods on that node could share it.
- **ReadOnlyMany (ROX)**: mounted read-only by many nodes.
- **ReadWriteMany (RWX)**: mounted read-write by many nodes. Needs storage that supports it, such as a network file system.
- **ReadWriteOncePod (RWOP)**: mounted read-write by exactly one Pod.

None of these makes it safe for two database servers to write the same files; that needs coordination inside the database.

## Why a claim can sit in Pending

```sh
kubectl get storageclass
kubectl describe pvc dispatch-data
```

This lab’s `standard` class uses `volumeBindingMode: WaitForFirstConsumer`.
That means no PV is created until a Pod that uses the claim is scheduled, so the storage can be made on the node where the Pod will run.
Until then, `describe pvc` shows an event such as “waiting for first consumer to be created before binding”.
Pending is normal here; read the events before assuming something is broken.

## Changing the database’s storage safely

A Deployment normally starts the new Pod before stopping the old one.
For a database, two copies briefly using the same storage is dangerous, so set the strategy to **Recreate**, which stops the old Pod first:

```yaml
spec:
  strategy:
    type: Recreate
```

## Proving the data survives

The workspace includes `storage-proof.py`.
It writes a unique marker into PostgreSQL along with the current Pod’s UID, deletes the database Pod, waits for its replacement, and reads the marker back.
It deliberately interrupts the database, so only run it in this practice lab.

```sh
python storage-proof.py
kubectl get pvc,pv
kubectl get pods -l app=db -o wide
```

A different Pod UID with the same marker shows the data outlived the Pod.

## Creating a PV yourself

Sometimes there is no provisioner, and you create the PV by hand.
This is **static provisioning**, and it comes up in the CKA exam:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: manual-pv
spec:
  capacity:
    storage: 1Gi
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /data/manual
```

A claim binds to it if it asks for `storageClassName: manual`, a compatible access mode, and no more than 1Gi.
`hostPath` uses a folder on the node, which is fine for practice but not for real data.

**Reclaim policy** decides what happens to a PV when its claim is deleted: `Delete` removes the storage, `Retain` keeps it for an administrator to deal with.

## Writing a StorageClass

A StorageClass names a provisioner and the settings it applies to every PV it creates:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-local
  annotations:
    storageclass.kubernetes.io/is-default-class: "false"
provisioner: rancher.io/local-path
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

- `provisioner` is the plugin that creates the storage; `kubectl get storageclass` shows which ones the cluster has.
- `volumeBindingMode: WaitForFirstConsumer` waits until a Pod uses the claim, so the volume is created on the node where that Pod runs.
- `allowVolumeExpansion: true` lets you grow a claim later by raising its `resources.requests.storage`; claims can grow but never shrink.
- The annotation `storageclass.kubernetes.io/is-default-class: "true"` makes a class the **default**, used by claims that do not name one. `kubectl get storageclass` marks it `(default)`. Only one class should be the default.

To change the default, remove the annotation from the old class and add it to the new one:

```sh
kubectl patch storageclass standard -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
kubectl patch storageclass fast-local -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

## What this does not protect against

This lab’s storage lives inside the kind node.
It survives Pod replacement, but deleting the cluster deletes it too.
Protecting against that needs backups, which the backup lesson covers.
