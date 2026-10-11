## Where Secrets really live

A Kubernetes Secret looks protected: `kubectl get secret` shows its values only as base64, and RBAC controls who may read it.
But base64 is an encoding, not encryption, and the API server stores every object, Secrets included, in **etcd**, the cluster's database on the control-plane node.
By default it stores Secrets there as plain data.
Anyone who can read etcd's files, its backups, or its network traffic can read every password in the cluster.

**Encryption at rest** makes the API server encrypt Secrets before writing them to etcd, and decrypt them when they are read back.
Applications and `kubectl` see no difference; etcd and its backups hold only ciphertext.

```figure
encryption-at-rest
```

## Seeing what etcd holds

You can read the raw stored value with `etcdctl`, the etcd client, which runs inside the etcd container on the control plane.
This prints only the first characters of the stored value, so no password appears on screen:

```sh
limactl shell "$DOCKYARD_CONTROL_PLANE" sudo sh -c 'crictl exec $(crictl ps --name "^etcd$" -q) etcdctl --endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key get /registry/secrets/dispatch/dispatch-database --print-value-only | head -c 24 | od -c | head -2'
```

An unencrypted Secret starts with `k8s` followed by a zero byte, the start of Kubernetes' plain storage format.
An encrypted one starts with `k8s:enc:aescbc:v1:key1:`, naming the provider and key that encrypted it, followed by unreadable bytes.

## The encryption configuration

The API server reads an **EncryptionConfiguration** file, passed with `--encryption-provider-config`:

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: BASE64_OF_32_RANDOM_BYTES
  - identity: {}
```

- `resources` says which kinds of objects to encrypt; here, Secrets.
- `providers` is an ordered list. The **first** provider encrypts every new write. When reading, the API server tries each provider until one succeeds.
- `aescbc` encrypts with AES using the key given; `aesgcm` and `secretbox` are alternatives, and production clusters often use `kms`, which keeps the key in a separate key management service.
- `identity` means "no encryption". Listed last, it lets the API server still read Secrets written before encryption was turned on. Listed first, it would turn encryption off.

Generate the key on the control-plane node, so it never lands in your workspace:

```sh
head -c 32 /dev/urandom | base64
```

The file holds the key itself, so keep it readable only by root: create it with `sudo`, in a folder with permissions `700`, and give the file permissions `600`.

## Wiring it into the API server

This is the same pattern as the authentication configuration in module 26: add the flag, and mount the file's folder into the API server's static Pod.

```yaml
- --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml
```

```yaml
volumeMounts:
- name: enc
  mountPath: /etc/kubernetes/enc
  readOnly: true
volumes:
- name: enc
  hostPath:
    path: /etc/kubernetes/enc
    type: DirectoryOrCreate
```

## Existing Secrets are still plain

Turning encryption on affects only what the API server writes from now on.
Secrets already in etcd stay plain until something writes them again.
Rewrite every Secret, unchanged, so each one passes through the new first provider:

```sh
kubectl get secrets -A -o json | kubectl replace -f -
```

```figure
reencrypt-secrets
```

## Fix it

1. Read the start of `dispatch-database`'s stored value with the `etcdctl` command above and see that it is plain.
2. On the control plane, create `/etc/kubernetes/enc/encryption-config.yaml` with an `aescbc` key you generate there, followed by `identity`.
3. Add the flag and the folder mount to the API server's manifest, and wait for `kubectl get --raw=/readyz` to print `ok`.
4. Rewrite all Secrets, then read the stored value again; it should start with `k8s:enc:aescbc:v1:key1:`.

## If something goes wrong

- **The API server does not come back**: on the control plane, `sudo crictl ps -a --name kube-apiserver` and `sudo crictl logs` on the newest container usually name the problem, such as a key that is not 32 bytes once decoded, or a path that does not match the mount.
- **New Secrets are still plain**: `identity` is listed first, or the API server has not restarted with the flag.
- **Pods cannot read their Secrets afterwards**: the configuration lost `identity`, so Secrets written before encryption cannot be read. Keep it last until every Secret is rewritten.
