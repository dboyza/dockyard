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
./scripts/check.sh
```

It runs, in order: Ruff lint and format checks and mypy, the non-integration Python tests, frontend lint, formatting, TypeScript, and unit tests, the structural curriculum audit in a temporary profile, and `pip-audit` plus `npm audit` dependency advisory scans.
It stops at the first failure.

Some backend checks bind local loopback sockets.
A restricted execution sandbox may require explicit local-network permission even though those tests do not contact an external service.

## Real-runtime verification

Run integration tests serially within each host environment.
They create disposable owned environments through the `lab_profile` fixture, which releases every lab even when a test fails.
Native test profiles use short paths under `/private/tmp` on macOS and `/tmp` on Linux to stay inside Lima's Unix socket length limit.

```sh
DOCKYARD_INTEGRATION=1 .venv/bin/pytest -x -q tests/test_curriculum_integration.py
DOCKYARD_INTEGRATION=1 .venv/bin/pytest -q tests/test_lifecycle_integration.py tests/test_retake_integration.py
DOCKYARD_INTEGRATION=1 .venv/bin/pytest -q tests/test_kubernetes_integration.py
DOCKYARD_VM_INTEGRATION=1 .venv/bin/pytest -q tests/test_linux_integration.py
```

The curriculum suite also records what a learner would see if they checked once, straight after the reference's last command.
Set `DOCKYARD_FIRST_CHECK_LOG` to a file path to collect one JSON line per unit, with the observations of any criterion that did not pass.
A first check that fails or reports stale, while a later one passes, means a learner who checks promptly would be failed for timing alone; fix the check rather than the reference.
Request checks retry briefly, checks re-observe while the runtime settles, and probes give a short grace period after a repair.

The curriculum audit starts every activity's real fixture, verifies its declared failure criteria, applies the reference, and checks actual passing behavior.
Additional suites test valid alternatives, ownership preservation, Stop/Resume, reset backups, and supported versus independent attempts.
A file-only curriculum audit does not replace runtime evidence.
Every suite cleans the labs it creates, including their images and anonymous volumes.
Afterwards, `./dockyard cache clean --yes` removes the pinned images the suites downloaded.

## Installed browser checks

Build and install before browser verification so the tests exercise the distributed assets.
The browser suites launch the installed CLI with a fresh authenticated local profile.
Chrome must be available.

```sh
./scripts/install.sh
DOCKYARD_INTEGRATION=1 npm --prefix frontend run test:e2e -- e2e/journey.spec.ts e2e/portability.spec.ts e2e/recovery.spec.ts e2e/reset.spec.ts
DOCKYARD_PROJECT_INTEGRATION=1 npm --prefix frontend run test:e2e -- e2e/project.spec.ts
npm --prefix frontend run test:e2e -- e2e/accessibility.spec.ts e2e/terminal-layout.spec.ts e2e/history.spec.ts
```

Test suites release their disposable profiles with `tests/release_profile.py`, which cleans every lab through its ownership records and deletes the profile only once nothing remains.
If it reports a kept profile, run the printed `lab clean --all` command; never delete such a profile by hand, because its records are the only safe way to find what is left.

The exam browser suite needs a prepared disposable profile.
The preparation script builds the CKAD release exam, applies its reference so a timed attempt scores 100, and records one earlier invalidated attempt for the history checks:

```sh
.runtime/installed/bin/python frontend/e2e/prepare_exam_profile.py .runtime/exam-check
DOCKYARD_EXAM_PROFILE=$PWD/.runtime/exam-check npm --prefix frontend run test:e2e -- e2e/exam.spec.ts
.runtime/installed/bin/python tests/release_profile.py .runtime/exam-check
```

It tests an actual scored submission, persisted flags and deadlines, and readable history after cleanup, and its second test cleans up the exam lab.
Never point it at personal learning progress.
Accessibility checks cover supported automated WCAG rules, both themes, narrow layouts, and confirmation dialogs; they do not certify complete accessibility or replace assistive-technology review.

## Authoring and version changes

Each activity owns its concept, task, debrief, prediction, progressive hints, starter, reference, and behavior contract.
Its optional checkpoint inherits a supplied application scaffold; individual source overrides stay explicit.
Use an independent mission to assess prior teaching and a distinct incident fault to assess diagnosis.
Keep explanations ahead of the prerequisites used by a task.
An exam's task titles and text come from its unit's `brief.md`, one `## N. Title (W%)` section per task in `exams.json` order; `exams.json` holds only weights, criteria, and remediation.

Ask of every check whether a learner could pass without doing what the lesson teaches.
When the key step leaves runtime evidence, check that evidence, as m07-reconciliation does with the ReplicaSet's creation and deletion events.
When the key step is a diagnosis, ask for a fact only the diagnosis reveals, as `finding.txt` does in m01-mission and the CKS investigations; never keyword-match explanatory prose.

A criterion's `diagnostic` is its general advice.
Its optional `cases` give advice for recognisable failures: each case is a regular expression searched in what the check observed, and the first match replaces the general advice.
Placeholders such as `{{container}}` in a case expand to their literal, escaped values.
`content/diagnostics.yaml` holds cases every activity on a runtime can meet, such as a missing lab container; they follow each criterion's own cases.
When a JSON check finds no value at its path, it reports `(absent)` and the path, and keeps the full output as details.
Reproduce each failure mode in a real lab and read the advice it produces before relying on a case.

### Lesson and primer figures

Lesson and primer Markdown embed a figure with a fenced block whose language is `figure` and whose only line is the figure ID.
`src/dockyard/content/figures.json` holds each figure's title, caption, screen-reader description, and optional steps; the catalog and the reference library reject unknown or malformed references, and every figure must be used somewhere.
The drawings live in `frontend/src/figures`, built from the shared SVG kit so they follow both themes; primer drawings are in `reference.tsx`.
After changing `figures.json`, regenerate the contracts; TypeScript then requires a drawing for every figure.
Review drawings with `npm --prefix frontend run dev` and `/gallery.html`, which shows every step; add `?theme=light` or `?figure=ID` as needed.
`./scripts/check.sh` compares every drawing and step in both themes with the reviewed images in `frontend/e2e/figures.spec.ts-snapshots`, which hide the surrounding text so only drawings are compared.
Each figure is shown alone while it is captured, so adding or removing a figure does not shift the pixel alignment of the others.
A failure leaves the expected, actual, and difference images under `.artifacts/playwright`; inspect them before deciding.
After an intended drawing change, run `npm --prefix frontend run test:figures -- --update-snapshots`, inspect the changed images, and commit them with the change.
Reference images are per platform because the interface uses system fonts; a platform without them is skipped with the command that creates them.
Draw on a 640-unit-wide canvas, keep text at its rendered size, and check both themes before relying on a figure.
The structural audit requires at least one figure in every lesson's concept and every foundation primer; missions, incidents, and exams stay figure-free so they do not hint at answers.
Use a stepped figure when the idea is a sequence or a change of state, and keep each figure's description complete enough to stand in for the drawing.
Each figure names one to four glossary terms in `terms`, shown as links beneath it; add a glossary entry first when a figure introduces a term the glossary lacks.
Following a term link remembers the figure and its step, and the reference desk's back button returns there; the reference library rejects unknown terms.

Change an activity revision when its learning contract or grading behavior changes after release.
Preserve older attempts as historical evidence and require reassessment for the new revision.
Update objective mappings when published objectives change, recording the source, checked date, and supported runtime versions.
Do not silently treat a newer Kubernetes release as the certification environment.

Pin new downloads to verified upstream identities and test their declared architecture.
Update both Kubernetes-version package manifests for both ARM64 and x86-64 when necessary.
The base toolchain manifest targets macOS; the Linux platform overlays pin native binaries and matching guest images.
Run `pwsh -NoProfile -File tests/windows-bridge.ps1` to validate the Windows launcher argument contract.
There is no hosted CI; run the fast checks on each platform you change, and remember that they do not replace actual Docker, VM, or Windows desktop verification.
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
