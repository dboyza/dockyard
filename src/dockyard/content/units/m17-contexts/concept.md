# Admission rules and runtime restrictions answer different questions

Pod Security Admission checks whether a Pod specification meets a namespace's selected policy level.
Baseline blocks common privilege escalations, while Restricted requires additional constraints such as non-root execution, dropped capabilities, an allowed seccomp profile, and disabled privilege escalation.
The namespace labels pin the policy version to v1.35 so the exercise does not silently change with a newer cluster.
Enforce rejects new violations, warn reports them to clients, and audit annotates API audit events when an audit backend is configured.
The local lab does not claim to collect an external audit log.

Changing a namespace policy does not evict an already running violating Pod.
Repair the workload template and complete a rollout as well as changing the admission setting.
The assessment tests both an acceptable server-side dry-run Pod and a nearly identical Pod that allows privilege escalation.
Dry-run reaches admission without creating a Pod.

An unrelated batch worker could declare these restrictions:

```yaml
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

The Pod-level context supplies shared defaults, while container-level fields constrain each process.
runAsNonRoot is a requirement; runAsUser selects the concrete numeric identity.
allowPrivilegeEscalation: false sets the no-new-privileges mechanism.
Dropping capabilities removes independent kernel privileges, and RuntimeDefault applies the runtime's default syscall filter.
None of these alone makes arbitrary code safe.

A read-only root filesystem is additional hardening and is not itself required by the Restricted policy.
Applications that need temporary or persistent writes must receive deliberately writable volumes.
Dispatch uses a bounded emptyDir at /tmp, Redis has its own temporary data directory, and PostgreSQL writes inside its persistent claim.
fsGroup supplies volume access for the chosen non-root process; it does not mean every host filesystem path becomes writable.

The checker inspects the live API process's numeric UID, effective capabilities, NoNewPrivs, Seccomp, and root mount flags through /proc.
That connects the declared fields to actual runtime behavior.
It then submits and completes a real job to prove the restrictions did not break the application.
