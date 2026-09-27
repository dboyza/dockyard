# Maintaining Dockyard

## Installation and ownership

The source installer builds the React assets and a Python wheel, then installs the wheel into `.runtime/installed`.
The `dockyard` launcher executes that installed package without changing the caller's working directory.
Source development uses `.venv`; installed profiles keep their own private runtime tools.
Application dependencies are recorded in `uv.lock` and `frontend/package-lock.json`.
Runtime tools and images use the separate pinned manifests in `src/dockyard/content`.
Source distributions include explicit application directories; private tools, dependency caches, and virtual environments must remain outside the archive.

Learner data lives in the selected profile, normally `~/Library/Application Support/Dockyard` on macOS or `~/.local/share/dockyard` on Linux/WSL.
Keep release verification in explicit disposable profiles.
Do not run broad Docker prune commands or operate on a resource merely because its name resembles Dockyard.
The cleanup adapters require recorded ownership and matching identities.

## Source setup

```sh
uv sync --locked --cache-dir .tools/uv-cache
npm --prefix frontend ci
```

The browser assets under `src/dockyard/static` and TypeScript contracts under `frontend/src/contracts.gen.ts` are generated.
Change their canonical source and regenerate them instead of editing generated output.
Generate API contracts with `.venv/bin/python scripts/generate_types.py`.
Build browser assets with `npm --prefix frontend run build`.

## Fast verification

```sh
.venv/bin/ruff check src/dockyard
.venv/bin/mypy src/dockyard
.venv/bin/pytest -q -m 'not integration'
npm --prefix frontend run lint
npm --prefix frontend run format:check
npm --prefix frontend run check
npm --prefix frontend run test
.venv/bin/python -m dockyard --data-dir .runtime/audit audit
```

Some backend checks bind local loopback sockets.
A restricted execution sandbox may require explicit local-network permission even though those tests do not contact an external service.

## Real-runtime verification

Run integration tests serially within each host environment.
They create disposable owned environments, and cleanup belongs in the test's `finally` block.
Native test profiles use short paths under `/private/tmp` on macOS and `/tmp` on Linux to stay inside Lima's Unix socket length limit.

```sh
DOCKYARD_INTEGRATION=1 .venv/bin/pytest -x -q tests/test_curriculum_integration.py
DOCKYARD_INTEGRATION=1 .venv/bin/pytest -q tests/test_lifecycle_integration.py tests/test_retake_integration.py
DOCKYARD_INTEGRATION=1 .venv/bin/pytest -q tests/test_kubernetes_integration.py
DOCKYARD_VM_INTEGRATION=1 .venv/bin/pytest -q tests/test_linux_integration.py
```

The curriculum audit starts every activity's real fixture, verifies its declared failure criteria, applies the reference, and checks actual passing behavior.
Additional suites test valid alternatives, ownership preservation, Stop/Resume, reset backups, and supported versus independent attempts.
A file-only curriculum audit does not replace runtime evidence.

## Installed browser checks

Build and install before browser verification so the tests exercise the distributed assets.
The browser suites launch the installed CLI with a fresh authenticated local profile.
Chrome must be available.

```sh
./scripts/install.sh
DOCKYARD_INTEGRATION=1 npm --prefix frontend run test:e2e -- e2e/journey.spec.ts e2e/portability.spec.ts e2e/recovery.spec.ts
DOCKYARD_PROJECT_INTEGRATION=1 npm --prefix frontend run test:e2e -- e2e/project.spec.ts
npm --prefix frontend run test:e2e -- e2e/accessibility.spec.ts e2e/terminal-layout.spec.ts
```

The exam browser suite additionally requires an explicitly prepared disposable exam profile in `DOCKYARD_EXAM_PROFILE`.
It tests an actual scored submission, persisted flags and deadlines, and readable history after cleanup.
Do not point it at personal learning progress.
Accessibility checks cover supported automated WCAG rules, both themes, narrow layouts, and confirmation dialogs; they do not certify complete accessibility or replace assistive-technology review.

## Authoring and version changes

Each activity owns its concept, task, debrief, prediction, progressive hints, starter, reference, and behavior contract.
Its optional checkpoint inherits a supplied application scaffold; individual source overrides stay explicit.
Use an independent mission to assess prior teaching and a distinct incident fault to assess diagnosis.
Keep explanations ahead of the prerequisites used by a task.

Change an activity revision when its learning contract or grading behavior changes after release.
Preserve older attempts as historical evidence and require reassessment for the new revision.
Update objective mappings when published objectives change, recording the source, checked date, and supported runtime versions.
Do not silently treat a newer Kubernetes release as the certification environment.

Pin new downloads to verified upstream identities and test their declared architecture.
Update both Kubernetes-version package manifests for both ARM64 and x86-64 when necessary.
The base toolchain manifest targets macOS; the Linux platform overlays pin native binaries and matching guest images.
Run `pwsh -NoProfile -File tests/windows-bridge.ps1` to validate the Windows launcher argument contract.
The CI matrix checks macOS, Linux ARM64, Linux x86-64, and the Windows PowerShell bridge.
A green contract matrix does not replace actual Docker, VM, or Windows desktop verification.
A new external build or bootstrap step must appear in cache readiness until its offline dependency closure is verified.
Never label a lab offline-ready merely because a base image exists.

## Release evidence

Use local commits, keep the worktree clean, and do not push or publish without explicit instruction.
For a candidate, record its commit, tool versions, package artifacts, test results, and the runtime source revisions actually exercised.
Run the fast verification and installed smoke checks against the final candidate.
Rerun affected real-runtime journeys when shared lifecycle code, fixture preparation, validators, or authored references change.
Record limitations and failures separately from passing observations.
The canonical running record is [runtime-evidence.md](runtime-evidence.md).

## Recovery and data portability

Progress archives contain historical evidence and portable drafts, never resource ownership records.
Imports validate ZIP boundaries and manifests before mutation, create a database backup, preserve existing notes, and keep imported drafts separate from active workspaces.
A completed checkpoint is immutable and carries its original support provenance.
Keep these boundaries intact when adding export formats or migrations.

After an interrupted operation, obtain the same exclusive operation lock before recovering its database status.
Do not infer that a stale status grants permission to delete resources.
The per-user capacity registry serializes cluster starts across registered profiles and retains the identity of each owning profile.
An unexpected file, symlink, missing identity, or mismatched resource should produce a recoverable diagnostic and preserve the resource.
