# Runtime feasibility evidence

This records development probes from 2026-09-26, not a release certification of the finished product.
The full approved curriculum and application remain under implementation.

## Verified behavior

- A dedicated WezTerm process opened the Dockyard workspace, ran a real zsh command, wrote its working directory to a probe file, and exited without changing existing tabs.
- kind 0.33.0 created a native ARM64 Kubernetes 1.35.8 cluster with a project-private kubeconfig.
- The node image was pinned to `kindest/node:v1.35.8@sha256:07b2536e30b803ed61d1677a79df6115f798ce64c80f9e22f6ed45afd09323c0` from the official kind release.
- Calico 3.32.2 ran on that cluster with kind's default CNI disabled.
- Live HTTP traffic between two pods succeeded, failed after a deny NetworkPolicy, and succeeded after an explicit allow rule.
- Lima 2.2.0 booted two native ARM64 Ubuntu 24.04 guests using the macOS VZ driver and user-v2 networking without host administrator changes.
- Both guests used no host mounts and a project-private LIMA_HOME.
- Direct guest-to-guest TCP communication succeeded.
- kubeadm, kubelet, and kubectl 1.35.8 initialized a real control plane and joined a separate worker.
- Both VM nodes became Ready after Calico installation.
- An etcd 3.6.6 snapshot was taken before deleting a test ConfigMap.
- Restoring the snapshot into a new data directory with a revision bump and updating the static pod's host volume restored the deleted ConfigMap.
- Both VM nodes were Ready after recovery.

## Implementation implications

The host kubectl is 1.37.0, so Dockyard must select its private matching 1.35.8 binary rather than relying on the user's PATH.
WezTerm inherited a stale UNIX socket in this agent environment; the reliable fallback launches a new process without WEZTERM_UNIX_SOCKET.
Lima on macOS used its platform cache despite XDG_CACHE_HOME, so the finished downloader should supply a verified local image path to keep downloads under app control.
Restoring etcd is not instantaneous; observe readiness and object recovery rather than imposing an arbitrary short sleep.
The probes verified a two-node administration cluster, not HA failover or version upgrades.
Those still require their own curriculum validation before release.

## Reproducible probes and local artifacts

- `scripts/probes/prepare-node.sh` prepares an owned Linux guest for Kubernetes.
- `scripts/probes/network.yaml` and `scripts/probes/check_network.py` test real network-policy enforcement.
- `scripts/probes/recover-etcd.sh` performs the destructive restore check only on the explicitly named disposable probe VM.
- `.artifacts/network-policy-proof.json`, `.artifacts/etcd-recovery.log`, and `.artifacts/wezterm-probe.txt` contain local observations.
- `.runtime/` and `.tools/` contain private development resources and are excluded from Git.

Tool archives were checked against their upstream checksum manifests before execution.
The Ubuntu image digest was verified by Lima.
