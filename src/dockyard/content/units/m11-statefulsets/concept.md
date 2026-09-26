# Stable identity is more than a Pod name

A StatefulSet gives each replica an ordinal identity, such as db-0, and uses a governing headless Service for network identity.
Its volumeClaimTemplates create a distinct claim for each ordinal.
Replacing db-0 changes the Pod UID while preserving its name and associated claim.
Stable identity helps stateful software locate its storage and peers, but it does not implement database replication or automatic failover.
Increasing PostgreSQL replicas alone would create independent databases, not a safe replicated system.

The supplied headless Service has clusterIP: None.
Its DNS answers point to endpoints directly instead of a Service virtual IP.
Dispatch clients still use a separate regular Service named db.
The two Services serve different discovery needs.

## Retention has two layers

StatefulSet persistentVolumeClaimRetentionPolicy controls whether generated claims are deleted when the StatefulSet is deleted or scaled down.
The defaults retain them, and this exercise makes both Retain choices explicit for review.
A PV's reclaim policy governs what happens after its claim is deleted.
With the local class's Delete policy, deleting a claim can ultimately delete its backing storage.
Retaining a claim and retaining a PV are related but distinct decisions.

```sh
kubectl get statefulset db -o yaml
kubectl get service db-headless -o yaml
kubectl get pvc,pv
kubectl get pod db-0 -o jsonpath='{.metadata.uid}'
```

The supplied replacement proof demonstrates stable storage using a real record and a different Pod UID.
It does not claim that this single-replica local database is highly available.
