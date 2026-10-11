# Workload and runtime security assessment

Eight tasks, each with its weight, on this lab's two-node kubeadm cluster.
Use the existing nodes; do not reset, rejoin, or rebuild them.
`$DOCKYARD_CONTROL_PLANE` and `$DOCKYARD_WORKER` hold the VM names for `limactl shell`; the Kubernetes node names add a `lima-` prefix.
Falco and gVisor are installed on both nodes.

## 1. Give the processing containers seccomp filters (10%)

In namespace `processing`, install the profile `profiles/no-chmod.json` from your workspace on both nodes where the kubelet finds Localhost profiles.
Run the `processor` container with that profile, and the `intake` container with the runtime's default profile.

## 2. Sandbox the template preview with gVisor (15%)

- Register the `runsc` runtime handler in containerd on the worker, and label the worker `sandbox.dockyard.io/gvisor=true`.
- Create a RuntimeClass named `gvisor` for `runsc` that schedules only onto nodes with that label.
- Run Deployment `template-preview` in namespace `untrusted` with it; it must still serve on port 8000.

## 3. Detect shells in application containers (15%)

Falco is installed on the worker but not running.
Write a rule in `/etc/falco/rules.d/dockyard.yaml` that alerts when a shell starts in a container, naming the namespace and the Pod.
Run Falco as a service that also starts at boot.

## 4. Contain the compromised workload (15%)

One workload keeps starting shells, reads Secrets in `dispatch`, and probes the metadata address.

- Write it into `finding.txt` as `NAMESPACE/NAME`.
- Revoke its access to Secrets in `dispatch`.
- Cut its Pod off from the network.
- Do not delete or restart its Pod; keep it for examination.

## 5. Find the changed replica and make the uploader immutable (15%)

One of the three `uploader` replicas in namespace `uploads` had its files changed while running.

- Write its Pod name into `tampered-pod.txt`.
- Give the uploader a read-only root filesystem, no privilege escalation, and writable volumes only for `/tmp` and `/var/cache/uploads`, still running as root.

## 6. Tidy the reports namespace's identities (10%)

- The `default` ServiceAccount in `reports` must mount no token and hold no permissions.
- No long-lived token Secret may remain in `reports`.
- `report-builder` must run as its own ServiceAccount that can only `get` the ConfigMap `report-settings`.

## 7. Shrink the worker's footprint (10%)

Stop the service on the worker that serves files to the network, and make sure it cannot start again.
Retire the account that can use `sudo` without a password.

## 8. Encrypt Pod traffic between nodes (10%)

Enable WireGuard in Calico so Pod traffic between the nodes is encrypted.

Throughout, keep the namespace `dispatch`, both Node objects, the `maintenance-sentinel` ConfigMap, and the stored job, and keep Dispatch processing jobs.
