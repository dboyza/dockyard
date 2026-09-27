# Debrief: Give an application a specific API identity

The workload uses its own ServiceAccount token to make an allowed request and encounter a denied request.
That result is stronger evidence than an administrator successfully listing Pods or a RoleBinding merely existing.

## Explain your result

Trace the subject, binding, role, resource, verb, and namespace that authorize the observed request.

## Transfer beyond this lab

Keep API authorization separate from network reachability: a namespace and a narrow Role do not automatically isolate application traffic.
