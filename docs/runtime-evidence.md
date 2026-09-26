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

The pre-existing fs-sim-x86 container retained its ID but changed from running to exited during the probe period.
Docker events show SIGTERM, then SIGKILL, stop, and exit code 137 at 15:20 UTC; OOMKilled is false.
No Dockyard command targeted this container, and it was not restarted or otherwise modified in response.
Do not report its running state as preserved.

## Reproducible probes and local artifacts

- `scripts/probes/prepare-node.sh` prepares an owned Linux guest for Kubernetes.
- `scripts/probes/network.yaml` and `scripts/probes/check_network.py` test real network-policy enforcement.
- `scripts/probes/recover-etcd.sh` performs the destructive restore check only on the explicitly named disposable probe VM.
- `.artifacts/network-policy-proof.json`, `.artifacts/etcd-recovery.log`, and `.artifacts/wezterm-probe.txt` contain local observations.
- `.runtime/` and `.tools/` contain private development resources and are excluded from Git.

Tool archives were checked against their upstream checksum manifests before execution.
The Ubuntu image digest was verified by Lima.

## First installed learner journey

The first authored lesson, `m01-processes`, now runs through the packaged browser and shared CLI on this Mac.
Its reference passed live checks for process state, lab identity, the published port, and the real HTTP response from Dispatch.
The real PTY shell and a dedicated WezTerm pane both opened in its isolated workspace.
An automated real-Docker regression verifies empty-starter failure, reference success, stop/check blocking, resume, reset backup, retained attempts, and owned-container cleanup.
The installed-wheel Chrome journey verifies one-time sign-in, keyboard tabs, hints, reference confirmation, persisted notes, 480/760/1440-pixel layouts, themes, and lab lifecycle actions.
A stopped-lab state regression and Docker's lowercase missing-resource response were reproduced and corrected.
The package was inspected to confirm compiled browser assets and authored lesson files are included.
These checks establish the first integrated journey only; they do not establish completion of the remaining curriculum or release gates.

## Docker foundations and image artifacts

All eight authored activities in Modules 1-2 passed the real-runtime starter/reference audit.
Each starter failed before the reference was applied, and each completed reference passed the relevant process, HTTP, identity, file-boundary, or non-root checks.
The image-cache exercise confirmed that the rebuilt and replaced application serves the new release.
The log/signal exercise grades a retained, gracefully stopped container, distinct from pausing a lab through Dockyard.
A multi-resource integration test confirmed stop/resume/cleanup across two containers, a network, and a volume while preserving an unlabeled fixture container by its recorded ID.
A separate process-death test confirmed OS operation locks are released after termination and interrupted operation records can be recovered.
The compatibility manifest now records digest-pinned Python, PostgreSQL, Redis, registry, BusyBox, and kind images.
These are development evidence for the currently authored units, not completion claims for Docker Modules 3-6 or later phases.

## Networks, persistent data, and Compose

Modules 3-5 now add twelve authored activities, bringing the verified authored inventory to twenty units.
The networking checks correlate bridge identities, caller-side DNS, private dependency ports, and the peer identity returned by a real request.
Storage checks create a temporary observation job and independently read its committed database through a read-only mount, then remove only that observation job.
Backup checks validate the archive database and the original seeded record in the restored service.
The storage permission starter initially passed because Docker populated an empty volume from the image; moving the deliberate fault after its initial mount produced the intended real write failure, and all four storage references then passed.
The supplied Compose application builds with hash-locked dependencies and uses PostgreSQL, Redis, a dashboard/API, and scalable workers.
All four Compose starters failed and their references passed, including a newly submitted job with the expected computed result and an independent direct PostgreSQL read.
The Compose audit completed in 42.22 seconds on this development run.
No claim is made yet for Module 6, Kubernetes course units, incidents, or exams.
