## Approve the partner plugin runner

Requirements:

- **Sandbox**: `plugin-runner` in `plugins` runs inside gVisor through a RuntimeClass named `sandboxed` that uses the `runsc` handler.
- **Secrets at rest**: the API server encrypts Secrets with a real provider, and `plugin-credentials` and `dispatch-database` are both stored encrypted in etcd.
- **Traffic between nodes**: Calico encrypts Pod traffic between the nodes with WireGuard, and real cross-node traffic uses it.

Dispatch must keep processing jobs, and the original namespace, nodes, marker object, and stored data must remain.
Never print or copy the encryption key or the partner token.

Write `isolation-report.md` describing each layer, the evidence that it works, and what it does not protect against.
Then compare it with `report-rubric.md`.
