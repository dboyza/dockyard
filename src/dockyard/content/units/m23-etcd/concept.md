## Two databases, two recovery boundaries

Etcd stores Kubernetes API state, including object identities, desired configuration, and Secrets.
PostgreSQL stores Dispatch jobs in the worker's persistent volume.
An etcd snapshot does not copy the contents of that application volume.
Recovering a Deployment definition cannot restore a deleted database row.
This exercise preserves a real job independently and requires both boundaries to survive.

A valid backup also needs a restore rehearsal.
Here you will take a live snapshot, inspect it, remove one original ConfigMap, and restore its original UID from the snapshot.
Recreating a ConfigMap with the same name and text will produce a different UID and will not pass.
The cluster is disposable and owned by this lesson; do not apply this procedure to another environment.

## Worked example: get below the API

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"
sudo crictl ps --name '^etcd$'
sudo cat /etc/kubernetes/manifests/etcd.yaml
```

The static manifest shows the member name, peer URL, TLS paths, and host directory mounted at `/var/lib/etcd`.
Use the running etcd container's ID with `sudo crictl exec ID etcdctl`.
A host CRI connection continues to work when kubectl cannot reach the API.
Use endpoint `https://127.0.0.1:2379`, CA `/etc/kubernetes/pki/etcd/ca.crt`, and the existing server certificate/key paths for this isolated local exercise.
Do not print or export private keys.
Production backup identities and permissions deserve a separate least-privilege design.

Run `etcdctl snapshot save /var/lib/etcd/dockyard-recovery.db` with those TLS flags, then inspect it using `etcdutl snapshot status /var/lib/etcd/dockyard-recovery.db -w json`.
The first command contacts the live server; the second examines the saved file.
Keep the file in the private guest because it contains cluster state and credentials.
Back in the host lab shell, `python -m dockyard.fixtures.recovery stage-loss` verifies the snapshot is readable, records its revision, and deletes only the original sentinel ConfigMap.
Confirm `kubectl get configmap maintenance-sentinel -n default` no longer finds it.

## Restore into a separate directory

Use `etcdutl snapshot restore`, not `etcdctl`, for the pinned etcd 3.6 generation.
Supply a new output directory `/var/lib/etcd/dockyard-restored`, the actual member name, and the peer URL from the manifest.
Set `--initial-cluster=MEMBER=PEER_URL` and `--initial-advertise-peer-urls=PEER_URL` for this single-member topology.
The restore verifies the snapshot hash by default; do not bypass that integrity check.
The currently running member can supply the tools while the offline restore writes a separate, unused directory.
Do not overwrite its active data directory.

Use `--bump-revision=1000000000 --mark-compacted` for this lab.
The revision advance prevents older restored revisions from being mistaken for current state; compaction invalidates watches so controllers relist.
The bump is a deliberate allowance for this small exercise, not a universal production sizing rule.
Restoration creates new etcd membership while retaining Kubernetes object identities from the snapshot.

Save the old manifest outside `/etc/kubernetes/manifests`.
Atomically change only the etcd volume's host `path: /var/lib/etcd` to the restored directory.
Leave the container mount path and its `--data-dir` unchanged: the host mount now presents the restored data there.
Kubelet will replace the static etcd container and the API will be briefly unavailable.
Do not store a second active manifest or backup YAML in the watched directory.

## Establish recovery with new work

Wait for the private API's `/readyz`, inspect the original sentinel UID, and verify that a fresh Pod receives a scheduler assignment.
Then complete a new Dispatch job and check that the earlier database sentinel still exists.
The assessment compares original identities, the recorded snapshot revision, the live etcd revision, new scheduling, and actual application behavior.
It does not award recovery credit for a snapshot file merely existing.

The supplied `python wait-control-plane.py` helper retries a read and a write against the recovering API, then observes a fresh scheduler assignment before deleting its disposable Pod.
Its source is available in the workspace so you can inspect the exact observations.
The scheduler may need longer to recover its watches and leadership than the API needs to answer a readiness request.
You may perform equivalent explicit checks yourself.
