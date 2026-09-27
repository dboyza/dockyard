# Dockyard 0.1.0 release validation

Validation date: 2026-09-27 UTC, on the intended Apple Silicon Mac.
The application candidate is local commit `1b920bd`; subsequent handoff commits update verification harnesses and documentation without changing the application source.
Nothing was pushed or published.

## Delivered scope

The installed package contains all 96 course units, 12 distinct incidents, four original eight-task timed practice exams, and 51 mapped CKA/CKAD objective records.
The 24 modules include four cumulative capstones and an evolving supplied Dispatch application.
Placement, a reference desk, predictions, authored feedback, progressive hints, reference review, notes, independent retakes, skill evidence, and spaced review are available.
The application uses the browser beside real WezTerm sessions, with Docker, kind, and native Lima/kubeadm environments.
Checkpoint continuation requires an explicit file selection and preserves previous workspaces.
Progress imports validate and preview the merge, and portfolio exports contain portable sources with provenance and observed evidence.

## Release checks

| Gate | Observed result |
| --- | --- |
| Structural curriculum audit | 96 course units, 12 incidents, four exams, 51 objective records, no issues |
| Backend regression | 86 passed; 121 real-runtime cases intentionally excluded from this fast run |
| Frontend tests | Four passed |
| Static checks | Ruff lint and formatting, strict mypy, ESLint, Prettier, TypeScript, and generated-contract consistency passed |
| Installed browser workflows | Lesson lifecycle, support interfaces, notes, diagrams, placement/review, progress transfer, and two-mission portfolio continuation passed |
| Accessibility | All eleven destinations in both themes, lesson/dialog interactions, and 760/480/320-pixel lesson layouts passed automated WCAG 2 A/AA and 2.1 AA checks |
| Fresh cluster and CKA audits | kind lifecycle and both CKA starter/reference audits passed together, three tests in 862.25 seconds |
| Docker lifecycle | Stop/Resume, blocked stopped-lab checks, reset backups, independent retakes, and unrelated-resource preservation passed |
| Installed failure recovery | Occupied port, unresponsive Docker endpoint, cancellation, concurrent clients, restored connectivity, and interrupted CLI preparation recovered |
| Real terminal | Installed CLI passed the first lesson in a real PTY and a new WezTerm pane; existing panes remained present |
| Installation | Locked source build and wheel installation into a new private environment passed; browser assets and all activities were present |
| Documentation | Relative links and anchors passed; wide/narrow light/dark README rendering and real product screenshots were inspected |

All 112 reference solutions were exercised against their declared real runtimes during implementation, with each intended starter failure checked before applying its reference.
The chronological [runtime evidence](runtime-evidence.md) records the staged audits, reproductions, corrections, and later passing observations.
These were staged audits, not one uninterrupted all-course test run on the final commit.
Affected shared lifecycle and authorization paths received fresh release-candidate audits.

Representative alternative solutions and shortcuts were tested where behavior could otherwise produce misleading credit.
These include equivalent Service selectors and named ports, equivalent disruption budgets, a surviving HA backend, restored-primary shortcuts, original volume identity, least-privilege scale permissions, and explicit Pod-log access.
The CKA maintenance reference also passed immediately after a real version upgrade followed by Stop/Resume.

The real timed CKAD journey persists its deadline and flags through a reload, rejects support during the active attempt, and reports measured weighted results.
Saved successful and technically invalidated reports remain readable after cleanup.
The deadline engine separately verifies automatic submission without an open browser and technical invalidation without a fabricated zero score.

## Package and environment

The wheel is `dist/dockyard_learn-0.1.0-py3-none-any.whl`, containing 1,490,379 bytes.
Its SHA-256 is `c3d5a4f4fb44c43988478fa13b29a43c94b72888f47bc6675a287f4aca33cc32`.
The installed launcher is `./dockyard`; ordinary use does not need Node.
Source installation uses `./scripts/install.sh` and the documented local prerequisites.

The validation host has 24 GiB RAM and runs ARM64 macOS with Docker 29.8.0.
The private lab matrix includes kind 0.33.0, Kubernetes 1.35.8, the adjacent native upgrade from 1.34.12, Lima 2.2.0, Helm 4.3.0, and Calico 3.32.2.
The canonical exact pins and integrity values live under `src/dockyard/content`.
The host's globally installed kubectl is not the lab version authority.

## Evidence boundaries and known limitations

- This release is validated for Apple Silicon macOS on this machine, with an 8 GiB maximum native profile budget and one active application cluster or native lab across registered profiles.
- Lessons, references, and progress are local, but some fresh labs still need network access for Python dependencies or native control-plane images.
  Full-course prefetch found no missing declared dependencies and explicitly classified 85 activities as having remaining network-dependent steps; it did not claim fully offline execution.
- The ordinary external shell has user privileges, so environment scoping and verified cleanup are not an operating-system sandbox.
- Automated accessibility checks and direct visual review do not replace comprehensive assistive-technology or learner testing.
  Functional checks do not establish learning effectiveness or guarantee certification results.
- The original practice exams cover CKA and CKAD preparation; full CKS preparation, production-scale traffic, cloud IAM, and multi-region failure domains are outside this release.
- The preexisting `fs-sim-x86` container retained its identity but had stopped during the early probe period, without a Dockyard command targeting it.
  Its running state was not preserved, and it was not restarted as part of this task.
  Later ownership-preservation checks passed using separately recorded unrelated fixture identities.
- README rendering was inspected locally with approximate Markdown styling, not on a published repository page.

Development lab cleanup used recorded identities through the runtime adapters and preserved source workspaces.
No global Docker prune, Docker Desktop resource change, shell dotfile change, default kubeconfig change, host administrator change, push, or publication was part of the release process.

## Begin learning

Run `./dockyard` from the repository, then choose **Practical placement**.
The benchmarks recommend a starting phase from observed work while keeping the complete course available.
Use the [user guide](user-guide.md) for daily workflows and the [maintenance guide](maintenance.md) for rebuilding and verification.
