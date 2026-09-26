## A bound claim is one stage of the path

This chapter's Dispatch checkpoint uses a real CSI-provisioned PostgreSQL volume.
The external provisioner creates a PV and records a driver-owned volume handle.
The attacher coordinates a VolumeAttachment when attachment is required, and the node-side driver exposes the filesystem to kubelet for the Pod's mount.
A bound PVC does not establish that the selected node has a usable driver or can access the underlying data.

The pinned hostpath CSI reference driver runs on the worker guest.
It stores data locally on that worker and is intended for learning and testing.
It does not provide shared storage, automatic replication, or a production high-availability database.
The StorageClass uses WaitForFirstConsumer so provisioning can take consumer placement into account, and Retain prevents automatic backing-volume deletion when a claim is removed.
Neither setting makes local data portable.

## Worked example: inspect the whole storage chain

```sh
kubectl get pod db-0 -o wide
kubectl describe pod db-0
kubectl get pvc data-db-0 -o wide
kubectl get pv
kubectl get csinodes
kubectl get volumeattachments
kubectl get pods -n dockyard-storage-system
```

Follow the PVC's `spec.volumeName` to the PV, then inspect `spec.csi.driver`, `volumeHandle`, and any node affinity.
Compare that information with the Pod's selector, scheduler events, and the node's CSI registration.
The driver process and the filesystem data reside on the worker; merely giving the control plane the same label would not move either one.

## The deliberate placement failure

The database was healthy and a sentinel row was written before its StatefulSet was changed to select the control plane.
Its replacement Pod cannot use the existing worker-local CSI volume correctly from that placement.
Keep the original claim and volume; recreating them would abandon the evidence that maintenance preserved data.
Repair the workload's placement to select a node capable of using the original storage.
A matching node selector or equivalent required node affinity can express that constraint.

StatefulSet rolling updates can remain stalled on an unhealthy replacement Pod after the template is repaired.
After verifying the repaired template, delete only the failed `db-0` Pod to let its controller recreate it from that template.
Deleting a Pod is different from deleting its PVC or underlying PV.
Wait for the database rollout and then the dependent API and workers.

## Prove the original bytes remain useful

The assessment checks the original claim and PV identities, CSI driver and volume handle, node registration, an attached VolumeAttachment, and the readable/writable PostgreSQL mount.
It then checks the pre-failure SQL sentinel and completes a fresh Dispatch transaction.
A replacement empty database can satisfy a TCP probe, but it cannot satisfy those continuity checks.
Record the specific layer that prevented service and the storage redundancy the reference driver does not provide.
