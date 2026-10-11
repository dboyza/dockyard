# CKS preparation track

Status: approved scope change on 2026-10-03; all six modules and both practice exams are written and passed real-runtime verification on 2026-10-10 (see [runtime evidence](runtime-evidence.md)).
The user asked for a CKS preparation track after the first release scope had excluded it.
This document is the design contract for that track; a module is complete only when its units pass real-runtime verification.

## Exam facts

Checked on 2026-10-03 against the CNCF curriculum repository and the Linux Foundation FAQ.

- The CKS curriculum is version 1.34, and the exam environment runs Kubernetes 1.35.
- The exam lasts two hours, is performance based, and requires an active CKA certification.
- The six domains and weights are Cluster Setup 15%, Cluster Hardening 15%, System Hardening 10%, Minimize Microservice Vulnerabilities 20%, Supply Chain Security 20%, and Monitoring, Logging and Runtime Security 20%.

## Approach

The track is a fifth phase, after cluster administration, because CKS assumes CKA skills.
Each of the six CKS domains gets one module, so a learner can see the exam's shape in the course.
Each module has three lessons and an independent mission, every lesson has a figure, and every check observes real runtime state.
Competencies that earlier modules already teach, such as Ingress TLS, NetworkPolicy, RBAC, Pod Security Standards, and cluster upgrades, are mapped to those units instead of being taught twice.
Node-level work runs on the existing Lima native clusters, because it needs real kernels, systemd, and static Pod manifests.
Image and manifest work runs on Docker or kind.

## Phase 5 modules

| ID | Module | Lessons | Independent mission |
| --- | --- | --- | --- |
| 25 | Cluster setup | CIS benchmark with kube-bench; node metadata and endpoints behind NetworkPolicy; verified platform binaries | Bring a cluster to an agreed benchmark baseline |
| 26 | Cluster hardening | Anonymous access limited to health checks; ServiceAccount token hygiene; finding and trimming over-broad RBAC | Close the access paths found in a security review |
| 27 | System hardening | Host footprint: services, ports, and kernel modules; AppArmor profiles; seccomp profiles | Confine a workload that must keep working |
| 28 | Microservice isolation | Secret encryption at rest; sandboxed containers with gVisor and RuntimeClass; Pod-to-Pod encryption with Calico WireGuard | Isolate an untrusted workload on a shared cluster |
| 29 | Supply chain security | Minimal base images; static analysis with kubesec and KubeLinter; signing images with cosign and verifying them before admission | Ship a signed, minimal, policy-compliant Dispatch release |
| 30 | Runtime security | Kubernetes audit logs; behavioral detection with Falco; immutable containers at runtime | Investigate an intrusion and contain it with evidence |

Two original timed practice exams, `exam-cks-a` and `exam-cks-b`, follow module 30.

## Competency map

| CKS competency | Taught by |
| --- | --- |
| Network security policies to restrict cluster level access | m17-network, i09-egress-regression, m25-endpoints |
| CIS benchmark review of etcd, kubelet, kubedns, and kube-apiserver | m25-benchmark |
| Ingress objects with TLS | m10-ingress |
| Protect node metadata and endpoints | m25-endpoints |
| Verify platform binaries before deploying | m25-binaries |
| Use Role Based Access Controls to minimize exposure | m17-rbac, m26-rbac |
| Service account caution: disable defaults, minimize permissions | m09-identities, m26-tokens |
| Restrict access to the Kubernetes API | m26-anonymous |
| Upgrade Kubernetes to avoid vulnerabilities | m21-upgrade |
| Minimize host OS footprint | m27-footprint |
| Least-privilege identity and access management | m17-rbac, m26-rbac |
| Minimize external access to the network | m25-endpoints, m27-footprint |
| Kernel hardening tools such as AppArmor and seccomp | m27-apparmor, m27-seccomp |
| Appropriate Pod Security Standards | m17-contexts |
| Manage Kubernetes Secrets | m09-secrets, m18-rotation, m28-encryption |
| Isolation techniques: multi-tenancy and sandboxed containers | m28-sandbox |
| Pod-to-Pod encryption | m28-wireguard |
| Minimize base image footprint | m29-minimal |
| Understand the supply chain: SBOM, CI/CD, artifact repositories | m16-pipeline, m18-images |
| Secure the supply chain: permitted registries, sign and validate artifacts | m29-signing |
| Static analysis of workloads and images | m18-images, m29-analysis |
| Behavioral analytics to detect malicious activity | m30-falco |
| Detect threats across infrastructure, apps, networks, data, users, and workloads | m30-falco, m30-mission |
| Investigate phases of attack and bad actors | m30-mission |
| Immutability of containers at runtime | m30-immutable |
| Kubernetes audit logs to monitor access | m30-audit |

The curriculum names Cilium and Istio as examples of Pod-to-Pod encryption.
Dockyard's clusters run Calico, which encrypts Pod traffic with WireGuard, so the lesson teaches the concept with Calico and explains how Cilium and Istio differ.

## Tools

Every tool is pinned by version and SHA-256 for ARM64 and x86-64, like the existing toolchain.

| Tool | Version | Where it runs | Source |
| --- | --- | --- | --- |
| kube-bench | 0.16.0 | Guest | GitHub release tarball |
| Falco | 0.45.0 | Guest | download.falco.org tarball |
| gVisor runsc and shim | release-20260928.0 | Guest | GitHub release tarball and SHA256SUMS |
| cosign | 3.1.3 | Host | GitHub release binary |
| kubesec | 2.14.2 | Host | GitHub release tarball |
| KubeLinter | 0.8.3 | Host | GitHub release binary |

Guest tools follow the existing offline rule: the host downloads and verifies each archive, extracts only the declared files into a canonical bundle, and copies the bundle into the guests, which never download anything.
A unit names the guest tools it needs, and only those are installed.

## Feasibility evidence

Checked on 2026-10-03 in a scratch Lima VZ guest built from the pinned Ubuntu 24.04 ARM64 node image, kernel 6.8.0-134.

- AppArmor is loaded with 117 profiles, and the kernel exposes BTF.
- gVisor `runsc` runs a sandbox on the systrap platform; `uname` inside reports `4.19.0-gvisor`. Its sidecar binaries must sit in a `gvisor-bin` directory next to `runsc`.
- Falco's modern eBPF probe loads, its bundled container plugin works, and the default rules detected reads of `/etc/shadow` on the host and inside a container.
- kube-bench 0.16.0 maps Kubernetes versions only up to 1.34, so lessons pass `--benchmark cis-1.12` explicitly and explain why.
- An AppArmor profile allowing reads everywhere and writes only to `/data` and `/tmp` ran a Python container in enforce mode, refused writes to `/etc`, and left Python working.
- A seccomp profile with `defaultAction: SCMP_ACT_ALLOW` and an errno rule for the `chmod` family put the container in filter mode 2 and refused `os.chmod` with EPERM.
- Through `ctr`, a gVisor sandbox booted and ran its command, but output and exit status did not reach `ctr`.
  Kubernetes uses the CRI path instead, and the m28-sandbox lesson verified a `runsc` RuntimeClass workload end to end in a real cluster.
- x86-64 guests were not exercised; the platform validation document records that boundary.
