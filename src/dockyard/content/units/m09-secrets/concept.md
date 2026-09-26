# Secret is a resource type, not a complete security system

A Secret separates sensitive values from ordinary application configuration and supports specific delivery mechanisms.
Base64 in the `data` field is encoding, not encryption.
Cluster encryption at rest, authorization, transport security, application behavior, and operational handling determine the broader protection boundary.
The later security modules examine those controls directly.

`stringData` is convenient for authored input; the API converts it to encoded `data`.
Never use production credentials in these disposable practice clusters.
The lab uses an automatically generated practice password and excludes credentials from portfolio exports.
Avoid printing decoded credentials, placing them in command history, or copying a runtime kubeconfig into the project.

## Worked example

```sh
kubectl describe secret dispatch-database
kubectl describe pod POD_NAME
kubectl exec deployment/dispatch -c api -- test -r /var/run/dispatch/password
kubectl logs deployment/dispatch --tail=20
```

The application reads `DB_PASSWORD_FILE` and opens a real database connection.
The projected volume is read-only, but the container user must still have permission to read it.
A correct Secret object with an incorrect key reference produces a delivery failure before successful authentication.
An environment-delivered credential has the same startup refresh limitation as other environment values.
Mounted Secrets update eventually, and the application must reopen the file to observe changes.
Database credential rotation requires coordinating the database and its clients, which is more than editing one Kubernetes object.
