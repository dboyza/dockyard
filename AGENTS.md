# Dockyard agent guide

This is a living document: keep it accurate, concise, durable, and deduplicated as the project evolves, with implementation details in docs.

## Product contract

- Build a personal, local-first Docker and Kubernetes learning workbench for Apple Silicon macOS, ARM64/x86-64 Linux, and Windows through WSL 2.
- Pair each browser lesson with an embedded terminal that runs the lab's real shell on this computer, and keep external terminals as an alternative.
- The embedded terminal became the default at the user's request on 2026-10-19; [terminal compatibility](docs/terminals.md) describes both paths.
- Teach beginners through advanced practice; offer an intermediate placement path.
- Follow [the implementation plan](docs/implementation-plan.md) and [the curriculum](docs/curriculum.md).
- Include Docker, practical platform engineering, and CKA, CKAD, and CKS preparation.
- CKS preparation was added at the user's request on 2026-10-03; [the CKS track](docs/cks-track.md) is its design contract.
- Keep all teaching, hints, assessment, and progress deterministic and local; include no AI, accounts, telemetry, or cloud service dependency.
- Use a calm professional visual design with accessible dark and light themes.

## Autonomy and boundaries

- The user approved the full plan through the planning review on 2026-09-26; implementation is authorized.
- Once implementation is authorized, make routine technical, editorial, naming, and visual decisions independently within the agreed scope.
- The user has authorized downloading tools and images into the project, starting Docker if needed, and creating/deleting app-owned practice containers, networks, volumes, clusters, and local VMs.
- Preserve unrelated resources, existing Docker settings, shell configuration, and the user's default kubeconfig.
- Scope lab operations by recorded ownership and explicit environment identity, never by a name prefix alone.
- Never run global prune/reset commands, access cloud accounts, incur charges, publish, or push unless explicitly instructed.
- Do not spawn subagents without new task-specific permission.
- Keep progress updates informative; do not request routine input during implementation.
- A genuine external approval or system credential cannot be assumed; continue independent work and report the exact blocker.

## Teaching and language

- Write as a patient teacher in plain English: explain the purpose, introduce terms before using them, show an action, then explain the expected observation.
- Keep learner-facing sentences to 30 words or fewer, use American spelling, and avoid filler words; `tests/test_plain_language.py` enforces this for lessons, hints, check messages, figures, and the learner documents.
- Teach container fundamentals before Dispatch; introduce Dispatch as the supplied background job application and distinguish its current stage from components added later.
- Explain the central ideas of each lesson and reference primer with embedded figures as well as prose, introducing one new idea at a time.
- Make prerequisites, workspace files, command placeholders, and completion criteria visible where they are needed.
- Give lesson code blocks no copy button; learners type every command themselves (user decision, 2026-10-19).
- Keep learner walkthroughs without hints or reference solutions separate from automated fixture audits.
- Describe passes as observed task results, not proof of reasoning, retention, or unaided work outside the app.

## Engineering and verification

- Prefer simple typed interfaces, one canonical curriculum source, reversible lab operations, and observed runtime evidence.
- Run `./scripts/check.sh` before committing; follow [the maintenance guide](docs/maintenance.md) for installed and runtime verification and [platform validation](docs/platform-validation.md) for the current evidence boundaries.
- Start bug fixes by reproducing through the real learner workflow.
- Verify shell behavior through real PTYs, and verify the embedded terminal in a real browser at real device scale; emulated scaling hides its WebGL output.
- Inspect screenshots with direct image-reading tools; browser automation is for the actual browser interface.
- Use disposable test profiles and app-owned labs; never test against learner progress.
- Release test profiles with `tests/release_profile.py`; never delete a profile that may still own lab resources.
- Verify every reference solution passes, every broken starter fails for the intended reason, and validators accept legitimate alternatives.
- Treat browser control as privileged local automation: authenticate sessions, validate origins, and expose only typed operations.
- Console WebSockets bypass the HTTP middleware, so they verify the exact origin and session cookie themselves.
- Every learner shell, embedded or external, has ordinary user privileges; do not describe environment scoping as an OS security sandbox.
- Do not treat Node Ready as networking proof; verify CNI/DNS readiness and actual cross-node traffic and policy enforcement.
- Keep node and Pod networks disjoint, and verify that native TCP/UDP forwarding exposes only the declared loopback ports.
- Keep runtime observations read-only and project explicit safe fields; never expose raw workload environment or Secret bodies.
- Use one complete sentence per physical line in long Markdown.
- Never use em dashes, add agent co-authors, or manually modify generated files or changelogs.
- Do not add hosted CI such as GitHub Actions; keep verification local.
- Create local commits after changes; only push when the user explicitly asks.
