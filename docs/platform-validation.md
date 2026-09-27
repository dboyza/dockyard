# Cross-platform validation

Candidate: Dockyard 0.2.0, local changes following the published 0.1.0 baseline.
Validation performed on September 26-27, 2026.
The original [release validation](release-validation.md) remains the historical macOS baseline.

## Implemented support

- Apple Silicon macOS retains its data location, Zsh sessions, and Lima VZ provider.
- Linux ARM64 and x86-64 use native pinned tools, XDG data locations, Bash sessions, and Lima QEMU/KVM.
- Windows runs the backend in WSL 2, with explicit distribution selection and Windows browser/WezTerm launch bridges.
- Docker image selection, archives, registry publishing, scanner inputs, and Kubernetes package names follow the host architecture.
- Lab Manager reports Linux memory, missing Docker plugins, and unavailable native virtualization prerequisites.
- Native VM identity uses filesystem creation timestamps, configuration hashes, device identity, and inode identity.
- Course prose and architecture exercises describe all supported hosts.

## Observed evidence

| Environment | Verification | Result |
| --- | --- | --- |
| macOS 26.6.2, Apple M5 Pro | Backend suite including platform paths, real Bash PTY, WSL argv, ownership, API, and progress contracts | 99 passed |
| Ubuntu 24.04 ARM64 VM | Backend contract suite, Python 3.12 | 99 passed |
| Linux x86-64 under Docker emulation | Backend contract suite, Python 3.14 | 99 passed |
| macOS | Frontend lint, formatting, TypeScript build, unit tests | Passed; 4 unit tests |
| macOS | Installed browser accessibility journey, both themes and narrow layouts | Passed |
| Ubuntu ARM64 | Source installer, installed CLI, authenticated browser workbench through a loopback-only SSH tunnel | Passed; readiness screenshot inspected directly |
| Ubuntu ARM64 | First process lesson and native-image artifact lesson, broken starters and passing references | 2 passed |
| Ubuntu ARM64 | Docker Stop/Resume, reset preservation, interrupted operation recovery | 3 passed |
| Ubuntu ARM64 | Supported mission followed by independent retake and preserved history | Passed |
| Ubuntu ARM64 | Real kind cluster, equivalent manifests, credential ownership, Stop/Resume | Passed |
| Ubuntu ARM64 with nested KVM | QEMU guest peer traffic, explicit API forwarding, undeclared TCP/UDP isolation, Stop/Resume, identity preservation, cleanup | Passed |
| Ubuntu ARM64 with nested KVM | Kubernetes 1.35.8 and 1.34.12 prerequisites installed with unusable guest package proxies | Both passed; containerd CRI and systemd cgroups verified |
| PowerShell 7.6.6 on macOS | Windows launchers with stubbed WSL: distro selection, spaced paths, literal arguments, installer dispatch, positional command forwarding, invalid mount rejection, nonzero exit propagation | Passed |
| Linux x86-64 emulation | kind, kubectl, Helm, Flux, Trivy, and Lima executable smokes | Passed; Lima run as an ordinary user |
| Linux x86-64 emulation | Dispatch Compose checkpoint Dockerfile and hash-locked binary Python dependencies | Built successfully with amd64 image metadata |
| Pinned upstream artifacts | All 23 container indexes include ARM64 and amd64; both Linux binary overlays and both x86-64 Kubernetes package sets | Downloaded/hash-pinned; Debian package architectures inspected |

The complete `m19-runtime` lesson passed through normal preflight, two QEMU/KVM guests, kubeadm initialization, Calico/DNS readiness, Dispatch deployment, the intended broken starter, the reference repair, final assessment, and cleanup.
Its final run completed in 204 seconds with Kubernetes 1.35.8.

## Corrections driven by runtime checks

The source installer initially failed because the validation checkout contained an extra bootstrap virtual environment.
Source archives now include explicit application directories and exclude dependency/build caches.
The final source installer was rerun after this packaging correction.

Ubuntu's base Docker package did not include Buildx, causing a later Dockerfile build to fail on `COPY --chmod` after VM creation.
The setup guide now names Buildx and Compose explicitly, and preflight/doctor report missing plugins before lab provisioning.
The private Linux validation VM received those packages; the macOS host package configuration was preserved.

The retake test could race Python's HTTP listener immediately after `docker run` returned on Linux.
It now waits for the actual health endpoint before requesting assessment.
The application still grades the state actually observed, rather than assuming a container is ready because its process exists.

Several older test fixtures assumed macOS temporary paths and VM architecture.
They now use the same platform boundary as the runtime.
Linux VM ownership keeps fractional creation timestamps rather than weakening the comparison to whole seconds or substituting mutable change time.

## Evidence limits

A Windows desktop and real WSL distribution were not available in this session.
The PowerShell and Python bridge contracts do not prove Windows GUI launch behavior, WSL localhost forwarding, or nested virtualization on a particular Windows computer.
Those remain explicit release smoke-test targets.

The x86-64 execution checks used emulation on ARM hardware.
A physical x86-64 host, x86-64 QEMU/KVM native lesson, and the new GitHub Actions jobs were not executed here.
The CI workflow is committed for subsequent runs and must not be reported as green until GitHub actually executes it.

This is a portability validation, not a repeat of all 112 original activity audits on every platform.
The original complete curriculum runtime evidence remains in [runtime-evidence.md](runtime-evidence.md).
These checks do not establish teaching effectiveness, production availability, or complete accessibility.

Local diagnostic artifacts are retained under `.artifacts/portability/` and excluded from Git.
They include contract logs, binary and image checks, installer logs, runtime journeys, PowerShell output, and the inspected Linux workbench screenshot.
