# Reuse the artifact, separate the environment

A common image can serve multiple environments without embedding their configuration or credentials in its layers.
Namespaces scope object names, so both environments can use a Service named `dispatch` and a Secret named `dispatch-database`.
Fully qualified service names distinguish those otherwise identical names.
Namespace organization alone does not block network traffic; later NetworkPolicy labs add that enforcement.

The mission combines observed configuration delivery, Secret-backed database authentication, and narrowly scoped API identity.
Document the difference between environment isolation in resource naming and enforced network or authorization boundaries.
