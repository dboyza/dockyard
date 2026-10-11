## Containers should not change while they run

A container image is built, scanned, and tested once, then run many times.
That only means something if the running container stays the same as the image.
If a process inside it can rewrite programs or configuration, an attacker who gets in can plant tools, change behavior, and stay hidden, and the image you scanned no longer describes what is running.

An **immutable container** cannot change its own files while it runs.
Anything it legitimately needs to write, such as temporary files or a cache, goes to a separate volume that disappears with the Pod.
When something must change, you build a new image and replace the Pods.

```figure
immutable-container
```

## Spotting a changed container

Replicas of one Deployment start from the same image, so their program and configuration files should be identical.
A quick way to compare them is a fingerprint: the checksum of a sorted list of every file's checksum.

```sh
for pod in $(kubectl get pods -n uploads -l app=uploader -o name); do
  echo "$(kubectl exec -n uploads "$pod" -- sh -c 'find /usr /etc /bin /sbin -xdev -type f ! -path /etc/hosts ! -path /etc/hostname ! -path /etc/resolv.conf -exec md5sum {} + 2>/dev/null | sort | md5sum') $pod"
done
```

`find ... -exec md5sum {} +` checksums every regular file in those folders, `-xdev` stays on the container's own filesystem, and the final `md5sum` condenses the sorted list into one value.
Kubernetes writes three files into every container itself, `/etc/hosts`, `/etc/hostname`, and `/etc/resolv.conf`, each holding that Pod's own name and addresses.
They differ in every replica by design, so the three `! -path` tests leave them out.
Identical replicas print the same fingerprint; a changed one stands out.
To see what changed in it, compare its file list with a healthy replica's.

```figure
replica-fingerprints
```

## Making the root filesystem read-only

The container's `securityContext` can mount its whole filesystem read-only:

```yaml
securityContext:
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

`readOnlyRootFilesystem: true` makes every write to the image's files fail with "Read-only file system", even for root.
`allowPrivilegeEscalation: false` stops a process gaining more privileges than its parent, for example through a setuid program.

Most applications still need to write somewhere.
Find out where, then give each place its own `emptyDir` volume, which is writable and is deleted with the Pod:

```yaml
volumeMounts:
- name: tmp
  mountPath: /tmp
- name: cache
  mountPath: /var/cache/uploads
volumes:
- name: tmp
  emptyDir: {}
- name: cache
  emptyDir: {}
```

The uploader writes partial uploads to `/tmp` and finished ones to `/var/cache/uploads`.
`kubectl logs` tells you if you missed a place: the application fails with a read-only error.

Changing the Pod template starts a rollout, which replaces every Pod, the tampered one included, with fresh copies of the image.

## Fix it

1. Fingerprint the three `uploader` replicas, find the one that differs, and write its Pod name into `tampered-pod.txt` in your workspace.
2. In `uploads.yaml`, make the container's root filesystem read-only, turn off privilege escalation, and add `emptyDir` volumes for `/tmp` and `/var/cache/uploads`.
3. Apply it with `python render.py uploads.yaml | kubectl apply -f -` and wait for the rollout.
4. Confirm `kubectl exec -n uploads deploy/uploader -- touch /usr/local/bin/test` fails, while the logs still show uploads being cached.

Record the tampered Pod's name before you apply; the rollout replaces it.

## If something goes wrong

- **The new Pods crash with `Read-only file system`**: the uploader writes somewhere without a volume. Read `kubectl logs` for the path and add an `emptyDir` for it.
- **All three fingerprints differ**: the command included files that differ in every Pod by design. Leave out the three files Kubernetes writes into `/etc`, and fingerprint only program and configuration folders, such as `/usr /etc /bin /sbin`, never `/tmp` or a volume.
- **You applied before recording the name**: `kubectl get events -n uploads` and the ReplicaSet history show the old Pod names, but you can no longer inspect its files.
