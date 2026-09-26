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

## Visibility and local delivery, 2026-09-26

All four Module 15 starter/reference audits passed in 621.91 seconds.
The observations connect actual request IDs to structured process logs, scrape both real API Pods, query live dashboard series, induce and clear a Prometheus latency alert, and compare bounded before/after SLO samples.
The dashboard uses a fixed three-minute time axis with explicit value scales and preserves expanded query explanations across refreshes.
Its updated implementation was rebuilt and observed against a fresh real cluster; the observation lesson passed again after fresh scrapes arrived.
Wide and 480-pixel screenshots were directly inspected at `.artifacts/observability-dashboard-final.png` and `.artifacts/observability-dashboard-narrow.png` without horizontal overflow.
These are bounded local signal and recovery checks, not a production SLO certification.

The Module 16 feasibility environment runs an app-owned smart HTTP Git server, private registry, and pinned Flux controllers.
A real Git push and independent clone succeeded without an external account.
An initial Docker Desktop publication failed when the registry used an automatically assigned host port; explicitly binding an allocated loopback port fixed engine-side access without changing Docker settings.
The Flux health check required read-only Pod and ReplicaSet access in addition to Deployment management; the scoped release identity retains no Secret or kube-system workload access.
The full rehearsal published a tested image, applied Git declarations, promoted one digest, observed an actual failed candidate image pull, and recovered through a new Git revert commit.
The first rehearsal also showed kubectl scale output retaining the pre-scale object; the evidence recorder now uses the actual API patch response to capture the zero-replica generation before reconciliation.
Fresh Module 16 starter/reference audits are in progress, so feasibility does not yet establish those four unit contracts.
The working catalog contains 64 course units; the verified curriculum checkpoint is 60 units pending that audit.

All four Module 16 starter/reference audits passed in 489.92 seconds after correcting the shared job verifier to address this checkpoint's StatefulSet database.
The checks independently exercise the published image's HTTP contract, compare source hashes and registry content, follow local/remote Git revisions into healthy Flux conditions, verify the scoped deployer, validate real drift/promotion/revert evidence, and complete a persistent job.
The working security chapter remains unverified at this point; the verified curriculum now contains 64 units.

## Enforced security and scanner preparation, 2026-09-26

All four Module 17 starter/reference audits passed in 358.51 seconds.
They observe real token-authenticated Pod reads and forbidden Secret/other-namespace reads, absent API/worker service-account tokens, two-node allowed and denied TCP paths with positive controls, and actual UDP/TCP DNS responses.
The admission exercise compares accepted compliant and rejected privilege-escalating server-side dry runs, then observes the API process's UID, capabilities, no-new-privileges flag, seccomp mode, and read-only root mount.
A real job completes through the restricted frontend, API, queue, worker, and persistent database.
The first starter attempted to add NET_RAW under Baseline and was correctly rejected before its intended exercise could run; the corrected starter uses the Baseline-permitted CHOWN capability and retains the intended admission/runtime faults.
The working and verified course inventory now contains 68 units; Module 18 is still being authored.

Trivy 0.74.0 and its 2026-09-26 database snapshot are pinned by artifact and installed-content hashes.
The actual scanner and CycloneDX inventory identified the deliberately unused PyJWT 1.7.1 fixture and CVE-2022-29217.
Additional base-image findings remain visible and are not represented as remediated by removing that fixture.
A second real archive scan succeeded with HTTP proxy endpoints pointing to an unavailable loopback port, offline scan flags, skipped updates, and telemetry disabled.
This verifies that prepared local inputs suffice for that scan; it is not a packet-capture claim about every possible scanner mode.
Scanner cache checks reject changed bytes, publication/schema mismatches, and symbolic links.

## Delivery pause and resume regression

A fresh real lifecycle test reproduced a Kubernetes 1.35 image authorization interaction after node restart.
The imported practice tag and the published registry release shared the same image configuration identity.
The node's ImagePulledRecord authorized the registry repository, while the local alias had no matching credential record and used pull policy Never.
The image remained fully present in containerd, but kubelet correctly treated that alias as inaccessible.
Published builds now include explicit release-version and lab-identity labels, separating release provenance from the imported practice configuration without disabling credential verification.
The fresh delivery lifecycle and shared-probe Module 8 mission regression both passed in 208.21 seconds.
The test checks retained Git revisions, identical local endpoints, resumed owned services, reconciled workloads, and a real persistent job.
Reference implementation: [Kubernetes image pull authorization](https://github.com/kubernetes/kubernetes/blob/v1.35.0/pkg/kubelet/images/pullmanager/image_pull_manager.go).

## Hardening module authoring checks

The first real backup rehearsal caught a missing delay_ms setting on the instrumented API's GET /jobs path.
The checkpoint now supplies that setting, and the hardening workflow validator checks the completed job through both PostgreSQL and the allowed frontend.
The four-unit audit is being repeated before the chapter is recorded as verified.

All four Module 18 broken-starter/reference audits passed in 410.84 seconds after the read-path correction.
They verify removal of the unused vulnerable package with an independent current-image scan, matching SBOM/report identities, and inspection of actual running consumers.
Credential checks test rejected old and successful current TCP authentication plus mounted consumer credentials.
Recovery checks authenticate the encrypted dump, reject a changed tag, preserve the original claim, compare distinct backing volume paths, and verify the saved completed marker through the frontend.
The compound capstone additionally repairs the denied frontend path and completes a new persistent job after recovery.
The verified curriculum now contains 72 units through the first three phases; Linux administration, incidents, exams, and the remaining application/release gates are still outstanding.
The installed 72-unit wheel passed the real Chrome/Docker journey in 11.9 seconds.
The backend regression passed 46 tests with five opt-in runtime tests skipped; Ruff, format, and strict typing checks passed.
The new Lima lifecycle adapter and its VM integration test are being developed separately and are not yet claimed as verified.

## Native Linux runtime foundation

The production Lima transport passed its two-guest lifecycle test in 49.50 seconds.
It verified native ARM64 guests, actual guest-to-guest HTTP, stop/resume, preservation of recorded disk/configuration identities, refusal after an external configuration change, and owned-guest cleanup.
The runtime uses a project-private VM home, verified local Ubuntu image and guest-agent inputs, no host filesystem mounts, and private loopback forwarding.
A longer development profile exposed Lima's temporary SSH socket limit; preflight now checks that longest path before creating any VM, and the recorded partial guest was cleaned before retrying.

A separate retained native pair initialized kubeadm 1.35.8 and joined its worker using CA-pinned discovery.
The observed guests run Ubuntu 24.04.4, kernel 6.8.0-134, and containerd 2.2.1.
The shared inline-credential client connected through the app-owned loopback endpoint without changing the user's kubeconfig.
The native CNI uses VXLAN, and its address detection follows Kubernetes InternalIP instead of assuming the guest interface is named lima0.
The first assumption failed visibly because this guest uses eth0; the corrected configuration passed both Calico and CoreDNS rollout checks.
Node Ready alone preceded those controller conditions and was not accepted as networking evidence.
A client on the control-plane guest reached a Service whose server ran on the worker, failed under an ingress denial, and recovered after an explicit client allow rule.
The native fingerprint remained stable without changes, detected a ConfigMap created outside the default namespace, and returned to its original value after that object was deleted.
Guest files and systemd service state are also included in the native runtime fingerprint.
Reference: [Calico IP autodetection](https://docs.tigera.io/calico/latest/networking/ipam/ip-autodetection).

The shared Kubernetes-client extraction passed the existing kind lifecycle and changed-credential rejection test in 90.10 seconds.
The backend suite passed 48 tests with five opt-in runtime tests skipped, and the focused native identity/environment guards passed six tests after the final cleanup adjustment.
Native curriculum units, HA behavior, supported minor upgrades, and guest package offline caching remain under implementation.
The official ARM64 package metadata lists 1.34.12-1.1 as an available kubeadm source version for the planned 1.35.8 minor-upgrade exercise.

## Offline native prerequisites

Fresh two-guest profiles installed the frozen Kubernetes 1.35.8 and 1.34.12 prerequisite sets with HTTP and HTTPS APT proxies set to an unusable loopback endpoint.
Both version cases passed in 77.44 seconds, including actual kubeadm and crictl versions, the CRI RuntimeReady condition, systemd cgroups, and owned-guest cleanup.
Each bundle contains 25 pinned Debian archives, approximately 115 MiB, with checksums recorded from the signed Ubuntu and Kubernetes repository metadata.
The installer uses dpkg directly; it cannot fetch omitted dependencies from a repository.
The initial APT --no-download path failed to acquire the supplied local archives and was replaced after reproducing that failure in a fresh guest.
This demonstrates cached prerequisite installation, not a fully offline cluster bootstrap or a packet-captured air gap.

The cache verifies each archive and its assembled bundle, repairs altered bundle bytes or incomplete bundle metadata, and refuses silent package-profile changes on an already prepared guest.
The focused cache/download regression passed nine tests, including changed bytes, interrupted metadata, resumed downloads, and integrity failures.
One cold-start attempt experienced two-minute SSH session delays in a guest; it eventually reached package installation, and the next two fresh profiles started and completed normally.
The delay was observed but its root cause was not established.

## Module 19: native node and control-plane boundaries

The four native administration units passed their complete broken-starter/reference audits in 750.06 seconds.
The course now has 76 authored units with successful real-runtime reference audits.
The new checkpoint runs the hardened Dispatch application on kubeadm guests, imports platform-specific images without host mounts, and stores PostgreSQL on a retained worker-local PV with explicit node affinity.
The native Pod CIDR is 10.244.0.0/16, separate from the 192.168.104.0/24 guest network.
A separate proof verified cross-node Service DNS/HTTP, actual ingress denial, and recovery after an explicit allow policy on this configuration.

The native checks observe an actual API process through CRI and its Linux cgroup, active kubelet services and fresh node leases, a separate private guest operator client, serving-certificate trust, and all four static control-plane components.
The application criterion submits a unique job through the frontend and verifies the worker's result through both HTTP and PostgreSQL before removing its test row.
The operator criterion requires CA trust and rejects insecure TLS bypass configuration.
The mission handoff is explicitly self-reviewed rather than semantically graded.

The real browser exposed an omitted native-resource group: the backend returned two VMs while the UI rendered zero cards.
The corrected view shows the actual guest names, state, CPU/memory allocation, and mount boundary, including observed stopped guests.
Direct screenshots were inspected at 1440 and 480 pixel widths; the narrow viewport was confirmed through window.innerWidth, with no horizontal overflow.
A new WezTerm pane showed the expected immutable lab ID, workspace, private LIMA_HOME, private kubeconfig, and the same two stopped guests.
The installed wheel's Chrome/real-Docker journey passed in 14.3 seconds, and the backend regression passed 50 tests.

The provider logs also exposed unintended automatic forwarding of guest ports onto host loopback.
The terminal ignore rule now explicitly matches every guest address and both TCP and UDP, after the allowed application/API rules.
A fresh two-guest lifecycle test proved an explicit API forward, cross-guest HTTP, refusal of an unrelated TCP forward, absence of an unrelated UDP echo, identity checks, stop/resume, and cleanup.
That test also froze systemd-logind, recovered it using a bounded D-Bus health check, and established a new SSH session without reusing the existing control connection.
The full boundary/lifecycle test passed in 108.82 seconds.
Reference: [Lima 2.2.0 forwarding rules](https://github.com/lima-vm/lima/blob/v2.2.0/templates/default.yaml#L482-L529).

Two fresh-boot observations identified an unresponsive guest login manager consuming a CPU core, with pam_systemd session requests timing out after two minutes.
A short trace showed a repeated nonblocking epoll loop; the underlying upstream defect was not established.
Guest initialization now checks the login manager and performs bounded recovery only if that service is unresponsive.
SSH authentication and the learner's Kubernetes services remain configured normally.

## Native HA construction proof

A separate owned four-guest profile initialized Kubernetes 1.35.8 with three stacked control-plane/etcd members and one worker.
All four nodes reached Ready, all Calico agents became ready, and CoreDNS became available.
A TCP HAProxy listener on the worker provided the stable private API endpoint, with the matching endpoint identity in the API serving certificates.
The primary API-server and etcd static manifests were then moved outside kubelet's manifest directory, and CRI inspection confirmed both containers had stopped.
A new ConfigMap was created, read, and deleted through the host's private load-balanced endpoint while the primary remained unavailable.
Direct etcdctl observations through each surviving runtime container confirmed a healthy endpoint and all three original voting members.
This establishes a surviving two-of-three quorum and useful API failover, not redundancy of the single load balancer, local database, or physical host.
The proof guests were paused before the separate fresh-profile course audits.

## Module 20 and native browser access

All eight Module 19 revision 2 and Module 20 starter/reference audits passed in 1108.40 seconds.
The course now has 80 authored units with successful real-runtime reference audits.
The HA audit additionally accepted a load balancer selecting only one surviving API server and rejected restoration of the failed primary as a substitute for failover.
A diagnostic reproduction found that clients and both original DNS replicas depended on the unavailable primary's local API connection.
The HA fixture now places diagnostic clients on a surviving control plane and spreads three CoreDNS replicas across the three control planes.
The primary API and etcd processes remain absent while quorum, fresh API writes, and Dispatch transactions pass.

A separate transport check found that forwarding an iptables-only NodePort did not establish the expected browser connection.
A restricted guest systemd service now forwards the declared application listener to the worker's NodePort, and every native workflow check first reaches the actual host-loopback browser endpoint.
Fresh native profiles passed these browser-path checks as part of the eight-unit audit.
Existing development VM profiles with older forwarding configurations require a reset to adopt this provider change.

## Reference desk

Five original primers cover terminal use, YAML, HTTP, DNS, and Linux, accompanied by 66 linked glossary entries.
Lesson links open the relevant term and preserve the learner's place on return.
The installed wheel's real-Chrome and real-Docker journey passed in 13.3 seconds, including glossary search, lesson navigation, and the compact mobile primer selector.
Direct desktop and 480-pixel screenshots were inspected in dark and light themes without horizontal overflow.
The backend regression passed 50 tests, and frontend lint, type checking, three component tests, and production build passed.
Maintenance-version selection and staging are implementation foundations; the actual Module 21 upgrade and maintenance audits are still pending.

## Portable checkpoint sources

A real completed Docker mission reproduced loss of a combined ConfigMap and Secret-template file during checkpoint creation.
The corrected exporter preserves environment-variable and inspected Helm value references, while removing documents with literal Secret values and recording each omission in the archive manifest.
Other documents in the same YAML file remain available.
The same real-mission reproduction then preserved the portable combined manifest byte for byte.
Focused regression checks also rejected literal-valued Helm expressions, nested Secret objects, and uninspectable credential templates.

## Structural release coverage

The `dockyard audit` command checks module composition, prerequisite cycles, reference entry points, intended starter failures, official objective links, incident inventory, and exam inventory.
It reports incomplete coverage until the remaining activities exist; it does not infer runtime success or teaching quality from file counts.
Its initial run found two superseded Module 17 IDs in the published-objective map, which now point to the authored admission and network-policy lessons.
All 24 Docker starters were prepared and assessed again in disposable real environments, and their observed failing criteria were recorded explicitly in their authoring contracts.
Boolean packaged probes retain the stricter false-value requirement, while direct Docker and HTTP checks require the named criterion to fail without imposing a boolean output format.

## HA concept interaction

The HA lesson includes a separate interactive model of endpoint routing and a three-member etcd majority.
The installed Chrome journey verified a route failure despite a surviving majority, a successful write after selecting a healthy API, and a reachable API unable to commit after losing the majority.
The complete installed-app and real-Docker journey passed in 15.0 seconds.
Direct 1440-pixel dark/light and 480-pixel light screenshots were inspected without horizontal overflow.
The model is explicitly distinguished from observations of the real practice cluster.

## Module 21: real cluster maintenance

The certificate lesson and both upgrade activities passed fresh-profile starter/reference audits in the first maintenance run.
That run completed three passing activities and one fixture failure in 1244.44 seconds.
The drain fixture passed after correcting a keyword argument, and its separate audit completed in 179.82 seconds.
The course now has 84 authored units with successful real-runtime reference audits.

Both upgrade activities began with actual 1.34.12 API servers and kubelets and finished with 1.35.8 API, static Kubernetes component images, and every kubelet.
The original namespace UID, Node UIDs, marker object UID, and SQL sentinel row remained intact, and fresh Dispatch transactions passed afterward.
An earlier reproduction advanced to worker maintenance before the restarted primary's reconciliation had settled and encountered an API interruption.
The reference now observes target-version node readiness, API readiness, and stable primary static-container identities for 30 seconds before advancing.
This two-node topology has planned API and worker-local database downtime; it does not demonstrate a continuous-availability upgrade.

The three-node drain activity evacuated the extra worker while retaining two available API replicas and the original database state on the other worker.
A disruption budget expressed as maxUnavailable 1 passed as an alternative to minAvailable 1.
Uncordoning the target was then rejected because the required maintenance boundary no longer held.
The certificate activity compared the renewed public leaf on disk with the certificate received over a fresh CA-verified TLS connection, while preserving the original CA and stored application data.
Its fixture starts with a valid certificate and teaches proactive renewal, rather than fabricating an expired-certificate outage.

The latest backend regression passed 52 tests in 7.45 seconds, and the installed 84-unit browser/real-Docker journey passed in 15.0 seconds with generated frontend contracts.
CSI infrastructure verification and Modules 22 through 24 remain under implementation.

## Native CSI construction proof

The pinned CSI hostpath reference driver ran inside a dedicated namespace on an owned worker guest with its real provisioner, attacher, resizer, node registrar, and liveness sidecars.
A WaitForFirstConsumer claim dynamically provisioned a CSI PV with a nonempty volume handle and an attached VolumeAttachment.
A nonroot consumer mounted the filesystem, wrote a unique sentinel, and read the same bytes after Deployment replacement.
The owned proof profile was stopped afterward.
This driver provides node-local reference storage, not production shared storage or automatic data movement between nodes.

Pristine upstream manifests, Apache-2.0 licensing, source checksums, and immutable OCI/ARM64 identities are bundled with the runtime.
The upstream v1.18.0 deployment template still references a v1.17.1 driver image; Dockyard explicitly selects the separately verified v1.18.0 image.
Snapshot and health-monitor add-ons are omitted from this teaching fixture.
Module 22 application integration and its fault/repair audits remain pending.

## Module 22: packet paths, Service programming, and CSI data recovery

All four infrastructure activities passed actual broken-starter and reference-repair checks on disposable native clusters.
The DNS activity restored the cluster zone and both kube-proxy agents, then resolved and contacted a newly created diagnostic Service.
The packet activity verified a cross-node HTTP failure from an exact raw-table PREROUTING rule dropping VXLAN UDP, then recovered actual traffic after removing that rule.
An earlier INPUT-hook fixture did not interrupt the traffic and was rejected by the starter audit; the final hook recorded dropped packets and failed the intended application checks.

The storage activity and compound mission used the CSI-backed PostgreSQL checkpoint rather than the earlier static local volume.
Repair preserved the original claim UID, PV UID, CSI volume handle, and pre-incident database row, then demonstrated a mounted writable database and a newly completed Dispatch job.
The compound fixture also repaired guest forwarding and frontend DNS policy.
Preparation waits for the previous attachment to detach and the frontend rollout to settle so the assessment does not begin amid fixture-induced resource transitions.
The four activities bring successful course reference audits to 88; later chapters remain under audit.

The actual Docker mission export also verified byte-for-byte retention of authored HAProxy, CoreDNS, and Helm helper source files.
The installed browser and real-Docker journey passed in 14.1 seconds after reproducing and fixing a historical-evidence heading that incorrectly used present-tense availability wording after the lab stopped.
Assessment evidence now includes its full date and describes the completed check explicitly.
