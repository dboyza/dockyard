## Pods that need a name of their own

Deployment Pods are interchangeable: they get random names like `dispatch-7f6f9-k7c5s`, and any one can be replaced by any other.
Databases and other clustered software often need more: each copy needs a stable name and its own storage that follows it.
A **StatefulSet** provides exactly that.

- Pods are named with a number: `db-0`, `db-1`, `db-2`. If `db-0` is replaced, the new Pod is also called `db-0`.
- Pods start in order, `db-0` first, and stop in reverse order.
- `volumeClaimTemplates` create a separate claim for each Pod, named after it, such as `data-db-0`. A replacement `db-0` gets the same claim back.

What a StatefulSet does **not** do is copy data between Pods.
Setting PostgreSQL’s replicas to 3 would give you three unrelated, empty databases, not one replicated database.
Replication is the database software’s job.

## Headless Services give each Pod a DNS name

A StatefulSet is paired with a **headless Service** (`clusterIP: None`), named in the StatefulSet’s `serviceName`.
It gives each Pod its own DNS name, such as `db-0.db-headless.dispatch.svc.cluster.local`, so peers can find a specific copy.
Dispatch itself still connects through the ordinary `db` Service; the two Services serve different purposes.

## What happens to the claims?

Two separate settings control whether data is kept:

- The StatefulSet’s `persistentVolumeClaimRetentionPolicy` decides whether its claims are deleted when the StatefulSet is deleted (`whenDeleted`) or scaled down (`whenScaled`). `Retain` keeps them; `Delete` removes them.
- Each PV’s **reclaim policy** decides whether the storage is deleted once its claim is deleted.

In this lab the storage class uses `Delete`, so if a claim goes, its data goes with it.
Keeping claims with `Retain` is what protects the data here.

## Look before and after

```sh
kubectl get statefulset db -o jsonpath='{.spec.persistentVolumeClaimRetentionPolicy}'
kubectl get service db-headless -o jsonpath='{.spec.clusterIP}'
kubectl get pvc,pv
kubectl get pod db-0 -o jsonpath='{.metadata.uid}'
```

`-o jsonpath` prints just the field you name, which is quicker to read than searching the whole YAML.
Run the last command before and after `python storage-proof.py`.
The name stays `db-0`, the claim stays `data-db-0`, but the UID changes, because it is a new Pod.
The marker the proof reads back shows the data survived.

A single database Pod on one node is still not highly available; if the node fails, the database is down until it comes back.
