# Dockyard implementation plan

Status: approved for autonomous implementation through the planning review, 2026-09-26.
This document describes the intended complete first release, not implemented capabilities.
Dockyard is the working product name; Dispatch is the application the learner evolves.

## 1. Agreed outcome

Deliver a polished local learning product that teaches the user to build, run, debug, secure, deploy, and operate containerized applications with Docker and Kubernetes.
The primary learner is this user, who has intermediate programming, terminal, Linux, and networking familiarity but wants a complete beginner-to-advanced path in these technologies.
The application combines browser-based learning with commands and file editing in a real external terminal.
It includes practical engineering, CKA and CKAD preparation mapped to published objectives, and advanced security exercises.
Full CKS certification preparation is a later extension, not part of this release.
No AI, account, telemetry, subscription, cloud cluster, or paid API is involved.

The release must be a complete course and operational application rather than a prototype with placeholders or a short sample curriculum.
Delivery phases are internal checkpoints and do not replace the full release scope.
Automated checks establish functional correctness and coverage; they cannot establish learning effectiveness or guarantee an exam result.

## 2. Confirmed environment and authority

Read-only inspection on 2026-09-26 found Apple Silicon, 24 GiB host RAM, roughly 749 GiB available disk space, and Docker client/server 29.8.0.
Docker reports 15 CPUs and approximately 7.75 GiB available memory.
Docker, kubectl, Node, npm, uv, Python, Git, and WezTerm are available on PATH.
kind, minikube, and Helm were not found on PATH during this inspection.
An existing container named fs-sim-x86 is running and must remain untouched.
No current kubectl context is selected; preserve the user's kubeconfig regardless of this initial state.
Recheck capabilities before implementation because this inventory can change.

The user explicitly authorized downloading tools/images into the project, starting Docker if needed, and creating/deleting only app-owned containers, networks, volumes, clusters, and local VMs during build and verification.
That authority does not include deleting unrelated resources, changing Docker Desktop resource settings, changing global shell configuration, publishing, pushing, or incurring charges.
Do not install a background login daemon or require host administrator access as a normal setup step.
Guest-root operations are confined to app-owned Linux VMs.

## 3. Learning experience

The home screen offers Continue, Course map, Incident practice, Exam practice, and Lab manager.
An optional practical placement assessment recommends a starting point without hiding the foundations or claiming mastery from a self-reported checkbox.
Prerequisites are visible and advisory; the learner can browse every lesson.
Glossary links and short terminal, YAML, HTTP, DNS, and Linux primers support missing background knowledge.

Every teaching unit has an observable outcome, prerequisites, a concept explanation, a worked example distinct from the task, a prediction question with authored feedback, a practical lab, progressive hints, a deliberate reference reveal, and a debrief.
Examples explain why commands and fields behave as they do, including common misleading symptoms and the consequences of alternative choices.
Progression moves from guided execution to partial scaffolding to independent missions.
Guided labs may supply commands after explanation; independent missions specify required outcomes without supplying the solution sequence.
Incidents use distinct failure scenarios and require diagnosis, rather than repeating a build task with renamed files.
Advanced modules include decision exercises about reliability, security, cost, and operational tradeoffs.

Record separate states for viewed, practiced, independently demonstrated, and review due.
Using hints or revealing a reference is recorded without punishment and does not become evidence of independent mastery.
An independent reassessment can upgrade a practiced skill to demonstrated.
Use a transparent local review schedule based on demonstrated skills, recent mistakes, and elapsed time, with no opaque AI scoring.
Short free-text explanations are saved with a self-review rubric, not automatically declared semantically correct.
The progress screen shows evidence and gaps rather than an unsupported exam-pass probability.

## 4. Real terminal workflow

The learner opens a unit in the browser, reviews the outcome and lab requirements, and chooses Prepare lab.
Dockyard provisions only the environment and fixtures appropriate to that exercise and displays readiness, download progress, and actionable errors.
For a cluster-installation lesson, it prepares clean Linux machines and package prerequisites while leaving the taught installation steps to the learner.
For an incident, it provisions a deliberately broken environment.
For an application task, it supplies application source while leaving the Dockerfile, Compose configuration, or Kubernetes manifests to the learner as appropriate.

Open terminal starts a new session in that lab's workspace with a clearly marked lab shell.
The shell receives an isolated KUBECONFIG, explicit Docker endpoint/context settings, app-owned tool PATH, workspace identifier, and lab identity without modifying global dotfiles.
Ordinary docker, kubectl, helm, git, and editor commands remain ordinary commands.
The browser does not need an embedded terminal or editor for release one.
If automatic terminal launch fails, the browser supplies an exact CLI entry command and the workspace path.
The learner may use any installed editor.

The CLI supports launch, doctor, lab prepare, lab shell, lab status, lab check, lab reset, lab stop, lab resume, lab clean, cache prepare, progress export, and progress import.
CLI checks and browser checks call the same assessment service and produce equivalent evidence.
The browser receives operation progress and observed lab status through a local event stream, then reconciles after reconnect.
Checking evaluates files and live behavior, not shell history or whether a particular command was typed.
The app never auto-types a solution into the terminal.

Keep a session's terminal identity immutable; switching the browser to a different lab does not silently retarget an existing shell.
Detect stale sessions and show which lab a check will inspect.
Changes outside Dockyard are reflected on refresh and Check.
Reset makes a complete workspace backup before replacement and requires a learner confirmation during normal app use.
Implementation and test harnesses can use explicit noninteractive options for owned disposable fixtures.
Closing the browser leaves the lab usable; Quit shows running lab resources, and Stop explicitly suspends the appropriate environment.

## 5. Dispatch: one application that grows with the learner

Dispatch is a small job-processing service with a browser dashboard, HTTP API, PostgreSQL database, Redis queue, and background worker.
The domain stays understandable: submit a job, observe its status, and retrieve its result.
Use a small supplied Python application with a simple supplied frontend; infrastructure is the subject, so writing business logic is not a prerequisite.
Introduce components only when their behavior creates a real learning need.

The journey begins with one local process and progresses through an image, durable data, a Compose stack, Kubernetes workloads, reliable networking and storage, controlled releases, monitoring, least-privilege access, and disaster recovery.
Maintain versioned checkpoints so a learner can enter a later chapter without completing every earlier chapter.
A successful mission snapshots the learner's infrastructure work with a clear provenance record.
Later missions can continue that work or use a known-good checkpoint without overwriting earlier attempts.
Incidents run in separate workspaces and disposable environments so they do not damage the learner's evolving project.
The final portfolio export includes authored manifests, Dockerfiles, charts, operational runbooks, and evidence of completed missions.
It excludes lab credentials, private keys, transient kubeconfigs, and cached images.

## 6. Curriculum and assessments

The baseline is 24 modules, each with three teaching labs and one independent project mission: 96 course units.
Add 12 distinct incident scenarios and four original timed practice exams, two CKAD-oriented and two CKA-oriented, for 112 substantial activities.
The final mission in each six-module phase is a cumulative capstone, giving four capstones within the 24 missions.
Placement diagnostics, primers, glossary entries, and spaced reviews are additional supporting material, not counted as course units.
Each teaching lab includes at least one deliberate troubleshooting or prediction exercise where it supports the objective; do not force identical stage counts when they harm teaching.
The detailed module map is in curriculum.md.

Every published CKA and CKAD objective must map to explanation, hands-on work, and an independent assessment, with explicit environment requirements.
Record the source URL, source revision, checked date, curriculum version, and validated runtime versions.
The current CNCF repository lists CKA and CKAD v1.35 curricula; verify the actual documents and objective mapping before freezing the implementation manifest.
Do not assume the newest Kubernetes release is the exam environment.
Use a tested supported version matrix, pin tool versions and image digests, and record an explicit adjacent-version upgrade pair for administration labs.
Treat changes to objectives or lab behavior as versioned curriculum changes rather than silently changing completed requirements.

Exam practice uses original performance tasks and published objectives, not copied exam questions.
Provide a visible timer, task navigation, per-task weights, allowed-reference policy, flag-for-review, and post-attempt remediation links.
Default practice length is 120 minutes; align instructions and tooling with verified public exam rules at implementation time without claiming to reproduce proctoring.
Persist deadlines and attempt state so reopening the UI does not reset the timer.
Technical failures pause or invalidate an attempt transparently according to a documented rule; never count an unavailable cluster as a wrong answer.
CKA administration tasks run in the appropriate VM environment.

## 7. Runtime environments and resource discipline

Use three explicit lab profiles: Docker/Compose, kind-based Kubernetes, and Lima-based Linux administration VMs.
Provision native ARM64 images and guests wherever possible.
Docker lessons use namespaced Compose projects, recorded resource IDs, project-owned labels, and loopback-bound application ports.
kind lessons use dedicated clusters and kubeconfig files, with single-node defaults and multi-node profiles only for objectives that need them.
NetworkPolicy lessons use a validated policy-enforcing CNI; a policy object existing is not proof of network enforcement.
Gateway and ingress lessons install the corresponding controller and verify actual routing.
Storage, metrics, autoscaling, and GitOps exercises explicitly provision and check the dependencies they teach.

Advanced node and control-plane administration uses app-owned Lima VMs with isolated storage, restricted host mounts, and unprivileged host networking where feasible.
The preferred VM network must permit node-to-node communication without host sudo and is a mandatory early feasibility test.
Use real kubeadm, containerd, kubelet, system logs, and etcd tools for installation, maintenance, and recovery objectives.
Use one control-plane guest and one worker for ordinary administration, with a separate three-control-plane/one-worker profile for hands-on HA behavior if required by the pinned objectives.
Validate HA endpoint failover and quorum behavior in that profile rather than grading a diagram as operational evidence.
Do not claim that deleting a kind cluster demonstrates a kubeadm upgrade or an etcd restore.
Keep application clusters and VM labs mutually exclusive by default to respect the available memory.
Stop only Dockyard-owned environments when switching profiles.

Initial targets are a 4 GiB workload budget within Docker, a 6-8 GiB aggregate VM profile, and a 40 GiB soft cache budget.
Measure actual consumption and revise these defaults autonomously while keeping adequate host headroom and preserving unrelated workloads.
Preflight checks report RAM pressure, free disk, tool versions, Docker health, architecture, ports, and image availability before provisioning.
Downloads are visible, resumable where practical, integrity-checked, and cached by version.
The learner can prefetch one module, one track, or the whole validated course.
Lessons and progress always work offline; a practical lab works offline only when its declared tools, packages, and images are cached.
The app displays cache readiness rather than silently claiming universal offline availability.

Resource ownership requires an inventory entry and matching resource identity, not merely a similar name.
Cleanup refuses unknown resources, presents its exact scope, preserves persistent learner files, and never runs global docker prune or resets Kubernetes globally.
Ordinary external shells retain the user's privileges; these conveniences do not constitute an OS security sandbox.
Administrative operations issued by Dockyard always use explicit endpoints, contexts, and ownership checks.

## 8. Application architecture

Use a React and TypeScript frontend built with Vite, a Python FastAPI service, a Python CLI, and SQLite for progress and operation state.
Bundle the compiled browser assets into the installable Python package so Node is needed for development, not ordinary use.
Use a foreground launcher that serves on loopback, opens the browser, and supports clean shutdown without registering a login daemon.
Provide a project-local launcher and a packaged installation path verified from a clean environment.
Use established accessible UI primitives where useful, with a small consistent custom token system rather than a large bespoke component framework.

One typed Python domain layer owns curriculum models, profiles, lab lifecycle, validation, progress, and export/import.
The browser and CLI are clients of that same behavior; do not maintain separate completion logic.
Define a narrow runtime adapter interface for Docker, kind, and Lima, and keep curriculum-specific checks separate from transport/process management.
Invoke tools through structured argument arrays with explicit environments, timeouts, output limits, cancellation, and process-group cleanup.
Use server-sent events for status updates and normal typed HTTP endpoints for actions.
Do not expose a browser endpoint for arbitrary shell execution.

Curriculum content lives in authored Markdown plus schema-validated metadata, starter fixtures, references, and check definitions.
Keep one canonical source of lesson text and contracts.
Generate any frontend types or indexes through reproducible scripts and never manually edit their outputs.
Validate every unit ID, prerequisite, link, resource requirement, hint, reference, and objective mapping in a curriculum audit command.

SQLite stores profiles, attempts, evidence, hints used, revisions, operations, resource inventory, and review schedules.
Use transactions, migration backups, bounded logs, and single-owner operation locks.
Keep user drafts as real files with atomic snapshot/export operations and conflict detection.
A progress migration preserves drafts and past evidence while marking materially changed objectives as due for reassessment.
Imports validate schemas, archive paths, size limits, collisions, and compatibility before changing state.

The local server uses a random per-install/session authentication mechanism, loopback binding, explicit host/origin checks, and CSRF protection for mutations.
Opening the browser must not put lasting credentials in URLs, logs, or exported artifacts.
Treat lesson content as trusted packaged data but sanitize rendered Markdown and reject arbitrary scripts.
Do not collect command history or secrets from the learner's shell.
Redact known lab credentials from logs and exclude them from export.

## 9. UI and accessibility

Use a calm professional workbench: slate surfaces, restrained blue accents, readable prose, clear spacing, and meaningful status labels.
Provide dark and light themes, visible keyboard focus, reduced-motion support, semantic landmarks, accessible controls, and contrast verified against WCAG AA targets.
The browser layout must work beside a terminal at narrow desktop widths without horizontal page scrolling.
Support useful reading on small screens while clearly keeping execution on the Mac.

The lesson view has a compact syllabus rail, a central reading/task area, and an optional evidence/context panel.
Keep one primary action for the current state: Prepare lab, Open terminal, or Check work.
Display the active lab identity, environment readiness, last-check time, and stale-evidence state near that action.
Expandable hints are incremental and references require a deliberate reveal.
Reference reveal does not overwrite learner files.
Evidence explains observed versus expected behavior and supplies relevant next diagnostic steps without automatically revealing the whole solution.

Other required screens are placement, searchable course map, project checkpoints, skill evidence, spaced review, incident browser, exam setup/session/report, lab manager, and settings/export.
Empty, loading, disconnected, no-Docker, downloading, canceled, failed, retrying, stale, and completed states are designed explicitly.
No decorative XP, artificial streak pressure, confetti, or unsupported mastery claims.
Use interactive diagrams where they explain image layers, port routing, desired state, selectors, storage, scheduling, or failure propagation.
Label diagrams as conceptual or live-observed, and show observation timestamps for live data.

## 10. Failure handling and assessment contracts

Lab lifecycle states are absent, preparing, ready, checking, stopping, stopped, failed, and cleaning.
Transitions are persisted, idempotent where possible, cancellation-aware, and recoverable after a server restart.
Partial provisioning leaves a recoverable operation record and only owned artifacts eligible for cleanup.
Poll readiness against a bounded deadline rather than fixed sleeps.
Show stale data during disconnect with a clear timestamp instead of presenting it as live.
One mutating lifecycle operation may own a lab at a time; use operation IDs to ignore late results.

Assessment outcomes are pass, fail, blocked, and stale.
Missing tools, stopped Docker, transient API unavailability, and resource exhaustion are infrastructure blockers, not learner mistakes.
Each check records unit revision, lab identity, relevant file hashes, observation time, criteria, expected behavior, observed evidence, and hint/reference usage.
Rerun or mark stale if relevant files or runtime observations change during validation.
Use health probes, application requests, resource inspection, network reachability tests, persisted-data checks, and recovery evidence as appropriate.
Do not pass an exercise solely from YAML text, resource names, or a successful process exit.

Accept legitimate alternatives that meet the declared behavioral contract.
Test known shortcuts that would create false positives, such as disabling security policy, deleting a failing workload, bypassing a service, or returning static success.
Keep evaluator capabilities separate from learner RBAC identities so checks can observe outcomes without accidentally granting the learner the required permissions.
Grade only evidence the system can actually establish; use explicit self-review for design explanations.

## 11. Delivery sequence and exit gates

### P0: Prove the environment and freeze contracts

Verify real WezTerm launch, isolated shell environment, Docker ownership preservation, a kind cluster, enforced network policy, and two communicating Lima guests without host admin changes.
Prove kubeadm initialization plus one recovery operation before depending on VM labs for the curriculum.
Freeze the compatibility manifest, source-to-objective map, curriculum schema, resource identity scheme, and typed runtime interface.
Choose a compatible alternative internally if the preferred tool fails, provided scope and isolation guarantees remain intact.
A genuine platform restriction must be reported; never replace required hands-on work with a pretend simulator.

### P1: Complete one learner journey

Build onboarding, a lesson, workspace preparation, external terminal launch, live behavior checking, authored hints, reference reveal, reset backup, progress persistence, and resume.
Use the first Dispatch Docker lesson as the integrated test case.
Pass that journey in the packaged application and real PTY before expanding the curriculum.

### P2: Complete Docker and project foundations

Deliver modules 1-6 with image, networking, storage, Compose, and release practices plus their independent missions and cumulative capstone.
Validate references, intended failures, cleanup, cache behavior, and export.

### P3: Complete Kubernetes application development

Deliver modules 7-12 with deployed Dispatch, storage, probes, jobs, routing, and the application capstone.
Complete useful live diagrams and evidence views using actual lab observations.

### P4: Complete platform, administration, and security

Deliver modules 13-24 including scheduling, packaging, observability, GitOps, access control, policy, kubeadm, maintenance, restore, and final operational handoff.
Validate all VM objectives and resource transitions on this Mac.

### P5: Complete independent assessment and review

Deliver all 12 incidents, four timed mocks, placement, spaced review, objective coverage reporting, and remediation links.
Audit the entire curriculum for explanation-before-use, distinct scenarios, coherent difficulty, and accepted alternative solutions.

### P6: Release hardening and handoff

Complete accessibility, UI polish, failure recovery, performance, offline-cache checks, package/install verification, documentation, and exact-commit release evidence.
Maintain local commits throughout and leave the repository clean without pushing.
Deliver the installed launch path, user guide, curriculum guide, maintenance instructions, real screenshots, validation report, and explicit known limitations.

## 12. Definition of done

- All 96 course units, 12 incidents, and four mocks are authored, reachable, and runnable with no placeholder lessons or simulated command outputs.
- All four phase capstones export useful Dispatch infrastructure and operational artifacts.
- Every CKA and CKAD objective has a dated explanation/lab/assessment mapping, with any actual coverage limitation surfaced rather than concealed.
- Every reference passes in its real declared runtime and every broken fixture fails for the intended reason.
- Validators reject representative false-positive shortcuts and accept valid alternatives.
- Docker, kind, and Lima suites use disposable profiles and prove preservation of unrelated resources.
- Fresh installation, first lesson, terminal launch, check, hint, reset, restart/resume, incident, exam, export/import, and cleanup pass as real end-to-end journeys.
- Terminal verification uses PTYs and real terminal tooling; browser verification uses the actual app.
- Browser layouts pass dark/light and narrow/wide checks, keyboard navigation, accessible naming, contrast checks, and reduced-motion behavior.
- Cancellation, concurrent tabs, interrupted provisioning, stale checks, missing tools, stopped Docker, port conflicts, and offline cache misses produce recoverable states.
- Backend tests, frontend tests, type checks, lint, formatting, curriculum audits, package builds, and installed-package smoke checks pass on the final commit.
- Docker Desktop settings, default kubeconfig, unrelated containers, existing repositories, and the learner's real progress are preserved.
- The final report separates verified facts, remaining limitations, and any external blockers.

## 13. Autonomous implementation agreement

After the user finishes this planning review and authorizes implementation, the agent should execute the full plan without routine product questions or milestone approval requests.
Choose package versions, compatible runtime alternatives, names, copy, layouts, tests, and internal structure using quality, simplicity, robustness, and maintainability.
Keep the user informed through progress updates without requiring a response.
Do not reduce curriculum breadth, silently defer VM labs, add AI/cloud dependencies, or substitute a prototype for the agreed release.
If an external credential, OS approval, unavailable dependency, or tool-enforced approval blocks an action, complete independent work and record the exact issue.
Do not claim that the user's autonomy preference bypasses platform approval controls.
Do not delegate; no subagents are authorized for this task.

## 14. Boundaries and sources

This release does not include full CKS preparation, hosted multi-user service, cloud-provider account labs, mobile execution, Windows/Linux support guarantees, a desktop wrapper, or an embedded terminal.
Local labs teach operational mechanisms, but cannot reproduce production traffic, failure domains, managed-provider IAM, or real multi-region availability.
Include explicit transfer notes explaining those differences at relevant advanced lessons.

- [Kubernetes learning environments](https://kubernetes.io/docs/setup/learning-environment/) supports local cluster practice using tools such as kind.
- [kind configuration](https://kind.sigs.k8s.io/docs/user/configuration/) informs cluster and port configuration.
- [kind macOS networking constraints](https://kind.sigs.k8s.io/docs/user/known-issues/) inform host access and routing checks.
- [Installing kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/) informs the separate administration environment.
- [Lima VM types](https://lima-vm.io/docs/config/vmtype/) documents native macOS virtualization options; suitability is still subject to P0 verification.
- [CNCF curricula](https://github.com/cncf/curriculum) provides the authoritative objective documents and versions.
- [CKA domains](https://github.com/cncf/curriculum/blob/master/cka/README.md) and [CKAD domains](https://github.com/cncf/curriculum/blob/master/ckad/README.md) define the coverage categories.

Planning sources were checked on 2026-09-26.
The implementation must pin exact upstream revisions in its coverage records and preserve required attribution when incorporating curriculum material.
