# Isolation report

## Findings and fixes

- `plugin-runner` ran partner code directly on the node's kernel. It now runs under the `sandboxed` RuntimeClass, backed by gVisor on the labeled worker.
- `plugin-credentials`, like every Secret, was stored in etcd in plain form. The API server now encrypts Secrets with `aescbc`, and all existing Secrets were rewritten.
- Pod traffic between the nodes travelled unencrypted in VXLAN. Calico now encrypts it with WireGuard.

## Evidence

- `dmesg` inside `plugin-runner` shows gVisor's messages.
- The stored values of `plugin-credentials` and `dispatch-database` start with `k8s:enc:aescbc:v1:`.
- The worker's `wireguard.cali` byte counters grow while jobs flow from the frontend.

## Remaining risks

- Only the worker can run sandboxed Pods; if it is drained, `plugin-runner` waits as Pending.
- The encryption key lives on the control-plane node; a KMS would keep it elsewhere.
