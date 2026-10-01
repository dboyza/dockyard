## Keep passwords out of ordinary configuration

A **Secret** is like a ConfigMap, but meant for sensitive values such as passwords, tokens, and keys.
It is a separate object type so that access to it can be controlled separately, and so tools treat it more carefully, for example by hiding values in `kubectl describe`.

Be clear about what a Secret does *not* do.
Its values are stored **base64 encoded**, which is a way of writing any bytes as plain text.
That is not encryption: anyone who can read the Secret can decode it in one command.

```figure
secret-encoding
```
Real protection comes from who is allowed to read Secrets, encrypting the cluster’s storage, and the application not printing them.
The security modules look at those controls.

## Creating a Secret

```sh
kubectl create secret generic demo --from-literal=password=example
```

In YAML you can use `stringData` to write plain values, and Kubernetes encodes them into `data` for you:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: demo
stringData:
  password: example
```

Only use made-up values in practice clusters.
This lab generates its own practice password, and Dockyard never includes it in exported work.

## Using a Secret

Exactly like a ConfigMap, a Secret can become environment variables, with `secretKeyRef`, or files, with a `secret` volume:

```yaml
volumes:
- name: database-credential
  secret:
    secretName: dispatch-database
    defaultMode: 0444
    items:
    - key: password
      path: password
```

Here the Secret’s `password` key becomes a file called `password` in whatever folder the volume is mounted at.
`defaultMode` sets the files’ permissions; `0444` means read-only for everyone.
When Kubernetes prints the YAML back, it shows the same value in decimal, `292`, which looks odd but means the same thing.

Files are usually the safer choice: environment variables are easy to leak through logs and error reports, and, as with ConfigMaps, they never update while the container runs.

To put several sources in one folder, use a **projected** volume.
It combines Secrets, ConfigMaps, and a few other sources into a single mount:

```yaml
volumes:
- name: app-config
  projected:
    sources:
    - secret:
        name: dispatch-database
        items:
        - key: password
          path: password
    - configMap:
        name: dispatch-settings
```

Mounted at `/etc/dispatch`, this gives one folder containing `password` and every key from the ConfigMap.

```figure
projected-volume
```

## This lab

Dispatch reads its database password from the file named in `DB_PASSWORD_FILE`, `/var/run/dispatch/password`.
The Secret volume asks for a key called `missing-password`, which does not exist, so Kubernetes cannot set up the volume and the Pod never starts.

Investigate without printing the password:

```sh
kubectl describe secret dispatch-database
kubectl get pods
kubectl describe pod POD_NAME
```

`describe secret` lists key names and sizes, never values.
The Events at the bottom of `describe pod` explain why a volume could not be mounted.

After fixing the key and running `sh run.sh`, confirm the file exists and the API can reach its database:

```sh
kubectl rollout status deployment/dispatch --timeout=90s
kubectl exec deployment/dispatch -c api -- test -r /var/run/dispatch/password && echo readable
kubectl logs deployment/dispatch --tail=20
```

`test -r` checks the file is readable without showing its contents.

## Changing a password is more than editing a Secret

If this password changed, PostgreSQL itself would need the new password too, and the API would need to pick it up.
Coordinating that is called **credential rotation**, and a later security lesson practises it.
