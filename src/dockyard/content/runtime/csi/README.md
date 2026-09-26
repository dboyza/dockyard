# Native CSI teaching fixture

These upstream manifests are preserved unchanged from the versions recorded in `sources.json`.
The hostpath driver is an Apache-2.0 licensed Kubernetes CSI reference implementation for a single node.
It does not provide production shared storage or move data between nodes.

Dockyard's `runtimes/native_csi.py` selects the provisioner, attacher, resizer, registrar, liveness probe, and driver containers.
It supplies a dedicated namespace, explicit permissions, guest placement, resource limits, and immutable imported image references.
Snapshot and health-monitor add-ons are outside this fixture's scope.
The upstream release archive is v1.18.0, while its deployment template still names a v1.17.1 driver image.
Dockyard explicitly selects the v1.18.0 image whose OCI and ARM64 identities were verified from the official registry.

See the runtime evidence document for actual verification status.
