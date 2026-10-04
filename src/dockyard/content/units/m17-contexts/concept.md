## Two layers of container security

This lesson connects two separate controls:

- **Pod Security Admission** decides whether a Pod is *allowed to be created* at all, based on rules set for its namespace.
- **Security contexts** are the settings on the Pod and its containers that actually *restrict the running process*.

```figure
admission-vs-context
```

## Pod Security Admission

Kubernetes has three built-in **Pod Security Standards**:

- **Privileged**: no restrictions.
- **Baseline**: blocks the most dangerous settings, such as privileged containers and using the host’s network.
- **Restricted**: also requires running as non-root, dropping all capabilities, a seccomp profile, and no privilege escalation.

You choose a standard per namespace with labels:

```yaml
metadata:
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.37
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: v1.37
```

- `enforce` rejects Pods that break the standard.
- `warn` accepts them but shows a warning to whoever created them.
- `audit` records them in the cluster’s audit log, if one is set up (this lab does not collect one).
- The `-version` labels pin the rules to a Kubernetes version, so a cluster upgrade does not quietly change them.

You can set these with `kubectl label namespace NAME pod-security.kubernetes.io/enforce=restricted --overwrite`.

Admission only checks Pods when they are created.
Tightening a namespace does not evict Pods already running, so you also have to fix the workload and roll it out.
When you apply the stricter label, kubectl warns you, for example “existing pods in namespace "dispatch" violate the new PodSecurity enforce level”, but those Pods keep running until they are replaced.

## Security contexts

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 12000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: report
    image: your-tested-image
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: [ALL]
```

- The Pod-level `securityContext` sets defaults for every container; the container-level one applies to that container.
- `runAsNonRoot: true` refuses to start the container as root; `runAsUser` picks the exact user number.
- `seccompProfile: RuntimeDefault` applies the container runtime’s standard filter on low-level system calls.
- `allowPrivilegeEscalation: false` stops the process gaining more privileges later.
- `capabilities.drop: [ALL]` removes root’s special powers, as in the Docker hardening lesson.
- `readOnlyRootFilesystem: true` makes the container’s own files unchangeable. It is extra hardening, not required by Restricted.
- `fsGroup` at Pod level gives a group access to mounted volumes, so a non-root process can write to them.

An application that needs to write somewhere needs a writable volume there.
Dispatch writes temporary files to an `emptyDir` at `/tmp`; Redis and PostgreSQL have their own writable data directories.

## Testing both layers

A server dry run sends a Pod to admission without creating it:

```sh
kubectl apply --dry-run=server -f some-pod.yaml
```

Check work uses this to confirm a compliant Pod is accepted and one that allows privilege escalation is rejected.
It also reads the running API process’s real restrictions from `/proc` (its user ID, capabilities, no-new-privileges and seccomp status, and whether the root filesystem is read-only), then submits a real job to make sure nothing broke.
