# Dockyard agent guide

## Product contract

- Build a personal, local-first Docker and Kubernetes learning workbench for this Apple Silicon Mac.
- Use browser lessons beside the real external WezTerm terminal.
- Teach beginners through advanced practice; offer an intermediate placement path.
- Follow [the implementation plan](docs/implementation-plan.md) and [the curriculum](docs/curriculum.md).
- Include Docker, practical platform engineering, CKA and CKAD preparation, and advanced security labs.
- Full CKS preparation is outside the agreed first-release scope.
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

## Engineering and verification

- Prefer simple typed interfaces, one canonical curriculum source, reversible lab operations, and observed runtime evidence.
- Start bug fixes by reproducing through the real learner workflow.
- Check terminal behavior using real PTYs and terminal tools, never browser-rendered terminal previews.
- Inspect screenshots with direct image-reading tools; browser automation is for the actual browser interface.
- Use disposable test profiles and app-owned labs; never test against learner progress.
- Verify every reference solution passes, every broken starter fails for the intended reason, and validators accept legitimate alternatives.
- Treat browser control as privileged local automation: authenticate sessions, validate origins, and expose only typed operations.
- An external learner shell has ordinary user privileges; do not describe environment scoping as an OS security sandbox.
- Keep AGENTS.md concise and durable; implementation details belong in docs.
- Use one complete sentence per physical line in long Markdown.
- Never use em dashes, add agent co-authors, or manually modify generated files or changelogs.
- Create local commits after changes; only push when the user explicitly asks.
