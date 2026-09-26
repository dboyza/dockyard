# Dockyard curriculum contract

Status: proposed for final planning review, 2026-09-26.
The module outcomes below are a scope contract, not claims of completed content.
Each row specifies three teaching labs and an independent mission, giving 96 course units across 24 modules.
The sixth module's mission in each phase is the cumulative capstone.
The phases form one evolving Dispatch project, with self-contained checkpoints for later entry.

## Phase 1: Container engineering

| ID | Module | Three teaching labs | Independent mission |
| --- | --- | --- | --- |
| 01 | Processes to containers | Process/image/container boundaries; lifecycle and inspection; logs, signals, exit codes | Run and diagnose the first Dispatch API container |
| 02 | Reproducible images | Dockerfile and build context; layers and caching; multi-stage builds and non-root runtime | Build a small reproducible Dispatch image |
| 03 | Container networking | Port publication and loopback; bridge networks and DNS; connection diagnosis | Connect Dispatch to an isolated dependency |
| 04 | Durable data | Bind mounts and volumes; permissions and lifecycle; backup and verified restore | Preserve Dispatch data across replacement |
| 05 | Multi-service applications | Compose services and configuration; readiness and dependencies; profiles and scaling workers | Run API, PostgreSQL, Redis, and worker together |
| 06 | Shipping containers | Tags, digests, and local registry; architecture and supply-chain basics; resource limits and runtime hardening | Capstone: deliver, break, recover, and document the Compose stack |

## Phase 2: Kubernetes application development

| ID | Module | Three teaching labs | Independent mission |
| --- | --- | --- | --- |
| 07 | Kubernetes mental model | API and reconciliation; namespaces, labels, and selectors; contexts, declarative updates, and inspection | Deploy Dispatch into a dedicated practice cluster |
| 08 | Workload design | Pods and Deployments; init/sidecar patterns; Jobs and CronJobs | Add a worker and scheduled maintenance job |
| 09 | Configuration and identity | ConfigMaps and environment; Secrets and delivery; service accounts and application access | Configure isolated Dispatch environments |
| 10 | Service communication | Services, endpoints, and DNS; ingress routing and TLS; Gateway API and HTTP routing | Expose Dispatch and repair broken routing |
| 11 | Stateful applications | PVs, PVCs, and StorageClasses; StatefulSets and storage lifecycle; backup and restore | Preserve database state through pod replacement |
| 12 | Reliable application releases | Probes and graceful termination; rolling updates and rollback; canary/blue-green patterns | Capstone: deploy and recover a safe Dispatch release |

## Phase 3: Platform engineering and security

| ID | Module | Three teaching labs | Independent mission |
| --- | --- | --- | --- |
| 13 | Scheduling and capacity | Requests, limits, and QoS; affinity, topology, taints, and tolerations; HPA, metrics, quotas, and disruption budgets | Keep Dispatch available under load and node drain |
| 14 | Packaging and extensions | Kustomize overlays; Helm values, releases, and rollback; CRDs and operator reconciliation | Package a repeatable environment-specific release |
| 15 | Operational visibility | Events, logs, and metrics; dashboards and actionable alerts; SLOs and incident evidence | Diagnose and explain a latency regression |
| 16 | Delivery automation | Local build/test/publish pipeline; GitOps reconciliation; drift, promotion, and rollback | Release Dispatch from a local Git source |
| 17 | Access and network security | RBAC and least privilege; enforced NetworkPolicy; Pod Security Admission and runtime security contexts | Restrict Dispatch without breaking its workflow |
| 18 | Hardening and recovery | Image scanning and SBOM interpretation; credentials, encryption concepts, and rotation; data recovery and operational runbooks | Capstone: harden Dispatch and recover a compound failure |

## Phase 4: Cluster administration and independent operations

| ID | Module | Three teaching labs | Independent mission |
| --- | --- | --- | --- |
| 19 | Linux and cluster internals | containerd, CRI, and cgroups; kubelet, systemd, and journald; certificates and control-plane components | Locate a failure across host, runtime, and Kubernetes layers |
| 20 | Building a cluster | kubeadm initialization; CNI and worker join; HA topology and endpoint behavior | Bootstrap a working cluster from prepared Linux guests |
| 21 | Cluster maintenance | Drain and node lifecycle; supported version upgrades; certificate renewal and component configuration | Upgrade and validate a disposable cluster |
| 22 | Cluster networking and storage | CNI and packet flow; CoreDNS and service proxy diagnosis; CSI behavior, scheduling, and storage failures | Restore an application affected by infrastructure faults |
| 23 | Control-plane recovery | etcd snapshots and verified restore; failed kubelet and static-pod recovery; unavailable API and control-plane diagnosis | Recover cluster state and prove application continuity |
| 24 | Operational handoff | Multi-layer triage under time pressure; capacity, reliability, and security decisions; runbooks, evidence, and exam workflow | Capstone: build, operate, recover, and hand off Dispatch independently |

## Twelve incident scenarios

Each scenario uses symptoms and failure mechanisms distinct from its teaching lab and has a reproducible broken state, an observable service impact, authored hints, and a validated repair.
Do not reuse the learner's main project environment for an incident.

1. A container exits successfully before doing its job because its process lifecycle is wrong.
2. A cached image build ships stale application content.
3. A Compose worker cannot reach its database after a configuration change.
4. A volume permission change breaks persistence while the service initially appears healthy.
5. A rollout stalls because startup and readiness behavior disagree.
6. A Service has no usable endpoints after a selector change.
7. An image cannot be pulled from the local registry under the configured identity.
8. A claim remains Pending because storage and scheduling constraints conflict.
9. A default-deny policy blocks DNS and a required dependency.
10. A workload cycles through memory failures and misleading restarts.
11. A node becomes NotReady after a kubelet configuration fault.
12. A control-plane incident requires a validated snapshot restore and a post-recovery check.

## Four original practice exams

- CKAD A: application build/configuration, deployment, service access, and diagnosis.
- CKAD B: a distinct task set emphasizing maintenance, workload patterns, security, and routing.
- CKA A: architecture/install, workloads, networking, storage, and troubleshooting.
- CKA B: a distinct task set emphasizing maintenance, recovery, and compound failures.

Each exam uses a 120-minute default, weighted performance tasks, independent fixtures, persistent attempt state, and a remediation report.
Blueprint weights should follow the dated official domain distribution, and every objective must appear somewhere in the full course assessment map.
The current CKA domain weights are 25% architecture/install/configuration, 15% workloads/scheduling, 20% services/networking, 10% storage, and 30% troubleshooting.
The current CKAD domain weights are 20% design/build, 20% deployment, 15% observability/maintenance, 25% environment/configuration/security, and 20% services/networking.
Sources: [CKA domains](https://github.com/cncf/curriculum/blob/master/cka/README.md) and [CKAD domains](https://github.com/cncf/curriculum/blob/master/ckad/README.md), checked 2026-09-26.

## Required curriculum evidence

Every unit must declare measurable outcomes, prerequisites, runtime profile, resource needs, versions, starter state, worked example, instructions, hints, references, checks, expected failure modes, and source attribution.
Every independent mission must define acceptable alternatives and what evidence earns completion.
Every capstone must connect to earlier Dispatch checkpoints and produce a useful export.
Every objective mapping must name the explaining unit, practicing unit, and independently assessing unit.
Never infer full CKA or CKAD coverage from these module titles alone; P0 must verify each objective against the pinned official documents and fill any gaps without reducing this scope.
HA behavior, network enforcement, restore correctness, and upgrades require real environment evidence wherever claimed.
If an objective requires an additional focused exercise, add it to the relevant module and update the inventory rather than hiding the gap.
