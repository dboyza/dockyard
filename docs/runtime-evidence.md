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

## Shipping and the first capstone

The three Module 6 teaching references passed live local-registry digest checks, full final-image layer inspection for a deliberately fake secret, and enforced cgroup/security observations.
The cumulative Docker capstone passed a real worker repair, registry-pinned application rollout, constrained API/workers, and a logical PostgreSQL restore of the original job into a separate database.
Its complete starter/reference audit took 31.37 seconds in the isolated development profile.
Passing missions now create immutable source-and-evidence archives with file hashes and an explicit exclusion manifest.
A portfolio test verifies source preservation, exclusion of environment/credential/backup files, note redaction, and immutability after later source edits.
The installed browser journey passed again with the complete Docker course packaged.
The full Docker regression is still recorded separately from these individual checks; Kubernetes runtime adapters and course content remain to be implemented.
The complete Docker regression subsequently passed all 26 tests in 118.96 seconds: 24 authored starter/reference journeys and two owned-resource lifecycle/preservation journeys.

## Kubernetes foundations, 2026-09-26

Implemented private kind clusters with recorded node identities, an app-owned kubeconfig, pinned tool integrity checks, Calico networking, bounded operations, and clean/stop/resume behavior.
The runtime rejects a modified kubeconfig authentication boundary before invoking kubectl.
Tool downloads support verified partial-file resume and preserve the prior installation when downloaded bytes fail their digest check.

The four Module 7 starters failed and their references passed against actual Kubernetes clusters: 4 tests passed in 162.97 seconds.
A separate end-to-end lifecycle test passed in 79.86 seconds after verifying preparation, a working application, stop, blocked assessment while stopped, resume, restored behavior, and rejection of an injected kubeconfig exec credential helper.
Fresh node imports initially exposed kind's multi-platform archive failure; exporting only linux/arm64 before import fixed the reproduced failure.
Resume testing exposed an API listener appearing before RBAC readiness and application convergence; the adapter now waits for API authorization readiness, and the lifecycle test observes convergence with a bounded deadline.

The browser's reconciliation model was inspected in Chrome and captured at `.artifacts/reconciliation-model.png`.
Deleting model Pod 1 left two desired replicas and one observed replica; advancing the controller created Pod 3 and restored the count.
This is explicitly labeled as a concept model separate from the real lab.
Course search was extended to taught concepts after a real browser search for reconciliation failed to find its lesson.

These are development gates, not evidence that the full planned curriculum or release is complete.

## Kubernetes workload checkpoint, 2026-09-26

All four Module 8 starters failed and their worked repairs passed against real clusters: 4 tests passed in 267.27 seconds.
The checks validate worker Deployment ownership and availability, submit a unique HTTP job, verify its transformed result independently in PostgreSQL, check DaemonSet coverage, observe shared init/sidecar configuration, and verify a completed maintenance Job's database effect.
The first full-stack bootstrap reproduced a `DB_PORT` collision with Kubernetes Service environment variables; the supplied manifests now disable implicit Service links and use explicit configuration.
The PostgreSQL volume at this checkpoint is deliberately ephemeral, which is stated in the teaching material and task limitations.

The Kubernetes browser journey prepared its own cluster and opened WezTerm pane 9 in the assigned workspace.
The terminal selected `kind-dockyard-b7dc909529a5` through its private kubeconfig, observed the zero-replica starter, repaired and applied the manifest, waited for rollout, and recorded a passing shared CLI assessment.
The native terminal inspection exposed an excessively long shell prompt, so the prompt now uses the unit, short lab identity, and final directory component.
CLI assessments now use concise human-readable evidence by default, with `--json` preserving full machine-readable observations.

Current local checks: 20 Python tests passed with real-runtime tests explicitly skipped, strict mypy and Ruff passed, frontend build/lint/Vitest passed, and the installed Chrome journey passed in 3.5 seconds.
The installed browser journey includes concept search, deletion/reconciliation behavior, a 480-pixel overflow check, and shutdown while the event stream remains open.

## Configuration, routing, storage, and releases, 2026-09-26

Module 9 adds ConfigMap and Secret delivery, a workload-token RBAC check, and an isolated preview environment.
Its four starter/reference audits passed in 263.81 seconds.
A strengthened combined audit of Modules 7-9 passed all 12 tests in 755.77 seconds, requiring explicitly declared starter failures to report false rather than accepting unrelated command errors.
The runtime fingerprint now includes learner resources outside the default namespace and routing/storage resources when available.
The lifecycle audit accepted a named Service target port and an additional matching selector, detected a ConfigMap change in preview, rejected an altered kubeconfig authentication boundary, and passed stop/resume and owned-network cleanup in 92.81 seconds.

Each new kind cluster has its own labeled Docker bridge.
The routing profile supplies pinned MetalLB, Traefik, and Gateway API components.
A real external Docker-network client reached an assigned LoadBalancer IP, strict certificate-validated curl reached the TLS ingress, and a Host-header request traversed Gateway API.
The initial TLS proof exposed a missing node-read permission in the ingress provider; the corrected controller passed without bypassing certificate verification.
All four Module 10 audits passed with live Service, EndpointSlice, NodePort, LoadBalancer, TLS, and Gateway observations.
The initial curriculum audit also caught the full-stack checkpoint omitting Pod identity from its health response; that response now identifies the actual serving Pod.

Module 11 verifies claim-to-volume binding, StatefulSet identity and retention, preservation of a unique database marker across a changed Pod UID, and logical restore onto a distinct claim and backing volume.
Its backup lesson passed, the claims lesson passed in 54.33 seconds, and the StatefulSet/mission pair passed in 113.29 seconds.
A transient first-query failure prompted a focused PostgreSQL reproduction: the image's temporary initialization server accepted a socket readiness probe while the TCP listener remained unavailable.
The supplied Kubernetes database probes now require TCP readiness, and previously committed Module 8 content revisions advanced accordingly.
The focused observation is recorded in `.artifacts/postgres-readiness-race.json`.
A broader affected-curriculum regression is still running at this development checkpoint.

All four Module 12 audits passed in 345.31 seconds.
They verify distinct startup/readiness/liveness behavior, an actual clean SIGTERM exit, failed ReplicaSet history and restored image, rolling availability settings, and separate stable/candidate responses through shared and preview Services.
These are local mechanism checks, not a claim of production availability under arbitrary traffic or failure conditions.

Independent retakes preserve prior evidence, notes, and source backups while starting a new assistance record.
A guided mission followed by an independent retake passed the real Docker audit in 2.83 seconds.
The installed browser journey passed in 10.4 seconds with real Docker lifecycle operations, retakes, storage-model interactions, narrow layout, and revision-aware progress.
The browser reproduction showed an older revision incorrectly labeled Demonstrated; current counts and labels now distinguish it as Review needed while preserving its historical assessment.
The storage model was directly inspected at `.artifacts/storage-model.png`.
The content currently contains 48 course units; platform engineering, VM curriculum, incidents, mocks, and remaining release gates are still implementation work.

The shared Docker regression passed all 27 selected tests in 131.86 seconds after these runtime changes.
The final installed browser rerun for this checkpoint passed in 10.6 seconds, including a single page-level heading and the revised source labels.
Python checks passed with 20 tests and 52 opt-in runtime cases skipped; Ruff, strict mypy, frontend lint, build, and Vitest passed.
The separate 20-unit Kubernetes regression remains in progress and will be recorded when complete.

## Metrics preparation proof, 2026-09-26

The two-node metrics proof returned live CPU and memory samples for both owned nodes.
Kubelet serving CSRs are checked for a valid signature, the recorded node username and subject, permitted server usages, and only that node's observed DNS/IP addresses before approval.
Metrics Server validates kubelet certificates against the cluster CA.
Its aggregation endpoint uses a separate app-generated serving certificate and a pinned APIService CA bundle; neither connection disables TLS verification.
Seven focused identity tests passed, including rejection of foreign addresses, expanded identities, client-signing usages, unrecorded nodes, and a damaged CSR signature.
The live proof is stored at `.artifacts/metrics-tls-proof.json`.
This is platform-runtime feasibility evidence; the scheduling and autoscaling curriculum is still being authored.

The affected 20-unit Kubernetes regression for Modules 8-12 passed in 1387.59 seconds after the TCP-readiness correction.
The metrics proof also drove a real HPA from one CPU-bound Pod to three, with current CPU utilization and scaling conditions captured at `.artifacts/hpa-proof.json`.

## Scheduling and observed resource maps, 2026-09-26

All four Module 13 starter/reference audits passed in the combined scheduling/packaging run before that run reached a separate Helm values-writer error.
The three-node drain reproduction captured RemoteDisconnected immediately after eviction, while the HPA evidence separately showed replacement Pod identities missing from the first metrics sample.
The supplied capacity workload now allows five seconds for endpoint removal before SIGTERM, and the rehearsal waits for measurements of the replacement Pods.
Three repeated drain observations recorded 89, 36, and 36 successful readiness samples with zero observed failures after the termination change.
Topology spread now includes pod-template-hash so rollout generations spread independently.
The final fresh-start Module 13 mission passed its resource, admission, placement, scaling, disruption, and drain criteria.
These samples establish the bounded local rehearsal, not a production zero-error guarantee.

The browser evidence panel now includes expandable measured details and a read-only resource relationship view.
A real Kubernetes observation returned 30 resources and 23 ownership, endpoint, or storage relationships without exposing workload credentials.
A real Docker networking lab returned two containers connected to its owned bridge.
The browser view preserves its last successful snapshot with an explicit unavailable message when that lab is paused.
Wide and narrow screenshots were directly inspected at `.artifacts/live-docker-map.png` and `.artifacts/live-map-narrow.png`, with no horizontal overflow at 480 pixels.
The installed browser journey passed in 11.9 seconds, including a terminal-side container repair, observed resource card, and expandable diagnostic evidence.
The backend suite passed 38 tests with 60 opt-in runtime cases skipped in 5.02 seconds; type, lint, formatting, and frontend build checks passed at this development checkpoint.

Module 14 and Module 15 are authored but remain under live runtime verification at this checkpoint.
The Helm audit reproduced an unsupported Path.open opener argument in the private values writer; the corrected builtin open call preserves mode 0600 and passed the Helm starter/reference audit.
The Kustomize starter/reference audit also passed; the operator and combined packaging mission remain in the running suite.

All four Module 14 starter/reference audits passed in 423.26 seconds after the values-writer correction.
They exercise real Kustomize rendering and applied configuration, Helm release history and rollback, a validated WorkerPool CRD, exact-UID ownership, controller repair of a scaled-to-zero managed Deployment, and job completion by the operator-owned workers.
A live observation during the broken packaging mission exposed a legitimate EndpointSlice with endpoints=null; the resource map now treats that as an empty endpoint set instead of failing the request.
The corrected observer returned 47 actual resources and 35 relationships from that lab.
The latest backend run passed 39 tests with 64 opt-in cases skipped in 5.52 seconds, and the installed browser journey passed in 15.0 seconds after rebuilding the wheel.
Module 15 remains in its live audit; it is not included in the verified 56-unit checkpoint.
