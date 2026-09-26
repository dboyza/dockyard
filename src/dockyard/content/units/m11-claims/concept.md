# A claim is a request, not a mounted database

A PersistentVolumeClaim requests capacity and access modes from a StorageClass.
The class describes provisioning behavior, including the provisioner, binding mode, and reclaim policy.
A PersistentVolume represents the storage that satisfies the claim.
The Pod must still reference that claim, and PostgreSQL must write into the mounted data directory.
A Bound claim beside an application using emptyDir provides no durability for that application.

This cluster supplies a standard class backed by node-local storage.
Its WaitForFirstConsumer mode delays provisioning until a consuming Pod can be scheduled, which allows storage placement to follow scheduling constraints.
A Pending claim with no consumer is therefore not necessarily a failure.
Read events before treating a status word as a diagnosis.

ReadWriteOnce means read-write mounting by one node, not necessarily one Pod.
ReadWriteOncePod is a different access mode available with supported CSI drivers.
Neither access mode makes a database safe for multiple independent writers without database-level coordination.
This lab uses one PostgreSQL process and the Deployment Recreate strategy when changing its storage mount.

## Worked example

```sh
kubectl get storageclass standard -o yaml
kubectl describe pvc dispatch-data
kubectl get pv
kubectl get deployment db -o yaml
kubectl get pods -l app=db -o wide
```

The supplied `storage-proof.py` writes a unique lab marker with the current Pod UID, deletes that database Pod, waits for a replacement, and queries the marker again.
Run it only in this dedicated practice environment because it deliberately interrupts the database.
The check later reads this evidence without deleting another Pod.

The local provisioner's storage survives Pod replacement but remains inside the kind node.
It does not protect against deleting the cluster or losing that node's storage.
Backup and replication solve different failure cases.
