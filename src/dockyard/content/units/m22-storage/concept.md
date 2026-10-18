## Following a volume all the way to the disk

In the storage module, a claim was Bound and the job was done.
With real storage drivers there are more steps, and each can fail on its own.
Kubernetes talks to storage through the **Container Storage Interface (CSI)**:

1. A **provisioner** creates the volume when a claim needs one, and records a **volume handle**, the driver’s own ID for it.
2. An **attacher** connects the volume to the chosen node, recorded as a **VolumeAttachment**.
3. The **node plugin**, running on that node, mounts it so the kubelet can give it to the Pod.

A Bound claim only proves step 1.

This lab uses the **hostpath CSI driver**, a reference driver that stores data in a folder on the worker.
It is meant for learning: the data exists only on that one worker, with no sharing or replication.
Its StorageClass uses `WaitForFirstConsumer`, so the volume is created where the Pod is scheduled, and `Retain`, so deleting the claim does not delete the data.
Neither of those makes the data able to move to another node.

## Worked example: inspect the whole chain

```sh
kubectl get pod db-0 -o wide
kubectl describe pod db-0
kubectl get pvc data-db-0 -o wide
kubectl get pv
kubectl get csinodes
kubectl get volumeattachments
kubectl get pods -n dockyard-storage-system
```

Follow the claim’s `spec.volumeName` to its PV, then look at the PV’s `spec.csi.driver`, `volumeHandle`, and node affinity.
Compare that with where the database Pod is trying to run and what its events say.
`csinodes` shows which nodes have the driver registered.

## What is broken

The database was healthy, and a known row was written.
Then its StatefulSet was changed to run on the control-plane node, where the driver and the data are not.
The replacement `db-0` cannot use its volume there.

Fix the StatefulSet so the database is placed on the worker again, with a `nodeSelector` or required node affinity.
Keep the original claim and volume; replacing them would lose the data.

```figure
csi-chain
```

A StatefulSet can stay stuck on a broken Pod even after you fix its template.
Once the template is right, delete only the failed `db-0` Pod so its controller recreates it:

```sh
kubectl delete pod db-0
kubectl rollout status statefulset/db
```

Deleting the Pod does not touch the claim or the volume.
Then wait for the API and workers to become ready.

## Proving the data survived

Check work confirms the claim and PV are the originals, with the same driver and volume handle.
It confirms the volume is attached and mounted on the worker.
It also confirms the known row is still there and a new job completes.
An empty new database could answer a connection, but it would fail those checks.
