# Rotate credentials across their consumers

A Kubernetes Secret represents sensitive configuration, but its base64 encoding provides no confidentiality.
Transport TLS protects an API connection; storage encryption protects stored data under a key management policy.
The credentials and the access rules still need to be scoped and rotated.
A Secret in a manifest can leak through source history, terminal output, exported diagnostics, or a misplaced backup.

Changing the Secret does not necessarily change the password accepted by the database.
Changing the database does not guarantee that every consumer has read the new value.
Environment variables are fixed at process creation; mounted Secret files update eventually, and an application may still cache them.
Plan the server transition and consumer refresh as separate operations.

For a different reporting service, the sequence is to provision a replacement credential, update the server's accepted identity, update the workload's Secret, refresh consumers, and test both the permitted and revoked credentials.
Systems that support overlapping credentials can reduce interruption by accepting both during a bounded migration window.
This practice database uses one password, so the rehearsal includes a brief interruption and explicit restart.

The supplied rotate.py helper uses PostgreSQL ALTER ROLE over standard input, applies the new Secret over standard input, and rolls the API and worker.
It stores the generated credential in a private file outside the workspace with mode 0600.
It never places the password in a command argument, Git file, or displayed report.
Inspect the helper to understand the sequence rather than memorizing its filename.

```sh
python rotate.py
kubectl rollout status deployment/dispatch
kubectl rollout status deployment/worker
```

The supplied database role is an administrator for this disposable teaching environment.
A production design should separate application permissions, migration permissions, and credential administration.
The credential protection demonstrated here does not add database transport TLS or enable etcd encryption at rest.
Those are distinct controls.

A successful rotation needs positive and negative evidence.
The new password must complete a real TCP authentication, the original password must be rejected, and both consumers must use the live Secret.
An error caused by a dead database is not evidence that the old credential was revoked.
The checker performs both attempts against the same reachable server and then completes an application job.

Keep a recovery route available before beginning rotation.
If the server changed but rollout failed, repair the consumers using the intended new credential; do not print passwords to compare them.
