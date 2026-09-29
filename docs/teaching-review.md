# Learner walkthrough and teaching review

Reviewed on 2026-09-27 using the installed macOS app, a separate learner profile, real terminal sessions, Docker containers, and local Kubernetes clusters.

## Scope and method

Seven activities were attempted from their concept pages, task briefs, and supplied workspace files.
No hint or reference solution was opened during those attempts.
The walkthrough deliberately inspected failures as well as successful results.
Source inspection followed the attempts when needed to explain a finding.
This was an expert walkthrough, not a study with beginner participants.
It does not establish that all 112 activities teach effectively or that a beginner would discover the same repairs unaided.

| Activity | Observed result | Teaching finding |
| --- | --- | --- |
| m01-processes | Started Dispatch, received its health response, observed a failed request after stopping, restarted, passed | The command works, but assumes familiarity with variables, mounts, ports, and the terminal before explaining them. |
| m01-lifecycle | Started the prepared instance, stopped and restarted it, confirmed its unchanged ID, passed | The worked example’s ID filter receives a container name and incorrectly returns an empty list. An immediate health request can also race application startup. |
| m01-signals | Sent a request, found its HTTP 200 log entry, stopped the container, observed exit code zero, passed | Useful practical distinction between successful shutdown and service availability; the prose introduces streams and signal terminology too abruptly. |
| m01-mission | Initial check failed; inspection found a one-shot command; repaired the container and passed | Reusing the first lesson’s launch recipe passes even with empty notes. The check proves recovery, not diagnosis or explanation. |
| m02-dockerfile | Wrote a Dockerfile, built an image, ran without a host mount, observed release dispatch-1, passed | Editing a file is an assumed prerequisite. The valid build produces an unexplained BASE_IMAGE default warning. Several different failures share the same vague diagnostic. |
| m07-reconciliation | Changed zero replicas to two and passed before deleting any Pod; then deleted one and observed a replacement with a new UID | The main learning experiment is not established by the check. Pod ownership and service behavior are checked correctly, but replacement observation needs explicit teaching and reflection. |
| m17-rbac | Initial check failed; removed Secret access; observed yes/no/no permission answers and passed real-token checks | “Supplied renderer” lacks an invocation. The inventory container waits for test requests rather than running the inventory application implied by the prose. |

The first Kubernetes replacement changed the selected Pod UID from `ae3d05e3-7f69-4574-8658-4e4c6a370403` to `1cba5bf5-66db-404a-b51c-0c43de6a7ee8` while the other Pod retained its UID.
The RBAC repair retained useful Pod reads and rejected Secret and other-namespace reads; simply breaking connectivity was not accepted as authorization denial.

## Findings addressed

### High: the app does not explain the project before asking the learner to operate it

The old Overview uses “Dispatch / API,” “persistence,” and “background processing” without explaining the application’s purpose.
The new introduction explains a submitted job, a worker, and a saved result in everyday language.
It distinguishes the first health-only service from the later system and states that the application code is supplied.

### High: navigation makes every feature compete with the next learning step

Eleven top-level destinations and a second list of four phases make the sidebar difficult to scan.
The revised sidebar has five primary destinations, with placement, exams, reviews, and saved projects grouped within the relevant page.
Search moves to the header, and the duplicate phase list and workspace avatar are removed.
A passing lesson now offers the next course activity.
On narrow screens, the lesson comes before the long supporting panel, with a direct link to its lab controls.

### High: declared prerequisites are invisible in the lesson

Activities already declare prerequisite IDs, but the browser never shows them.
Lessons now show those activities before the explanation and link to terminal, YAML, or Linux help as appropriate.
The opening lesson explains shell variables and line continuation locally, and the terminal primer now teaches text-file creation.
The Dockerfile lesson identifies the file to edit and explains the observed build warning.

### High: an operational pass is presented too strongly as understanding

The first mission can pass without a diagnosis in notes, and reconciliation can pass without a deletion experiment.
These are actual gaps between a successful system and the broader learning outcome.
The app now describes the recorded result as task behavior, explicitly says notes and predictions are not graded, and explains the limits of “without help” to in-app hints and references.
Debriefs ask the learner to explain and transfer the result before moving on.
The reconciliation debrief explicitly sends learners back to the experiment if they skipped it.
No keyword check of prose was added: matching words would not establish understanding either.

### Medium: failure feedback is harder to use than it needs to be

Failures now appear before passing criteria, with the suggested next check visible and raw expected/observed output behind Check details.
The live resource diagram follows the assessment rather than displacing the result.
Loopback-binding, packaged-source, release-version, and RBAC diagnostics now name a useful observation and repair direction.
Incorrect predictions say they are incorrect rather than responding with the ambiguous “A useful distinction.”

### Medium: lesson language sounds like a specification rather than a teacher

The seven reviewed activities now explain their purpose, introduce terms in context, and give concrete observations to look for.
The first Kubernetes lesson explains the cluster, namespace, Pod, ReplicaSet, Deployment, manifest, supplied script, placeholder, and watch command before relying on them.
The permissions lesson describes the actual practice client and renderer, and distinguishes useful access from denied access.
Core navigation, progress, review, project, and placement copy has also been simplified.
A teaching-language contract in AGENTS.md keeps these expectations visible for future authoring.

### Medium: terminal controls can get stuck during preparation

A real installed browser journey reproduced a race where terminal discovery ran before the workspace existed.
The control retained its preparation error after the lab became ready.
Terminal discovery now waits through preparation and refreshes when the lab identity or state changes.
A focused regression check covers that transition in addition to the real browser journey.

## Course-wide review (2026-09-28)

After the first seven activities, every remaining course unit, incident, and practice exam was reviewed the same way.
Each was attempted from its concept page, brief, and workspace files without hints or reference solutions, in a disposable profile.
Per-activity results are in [the coverage ledger](teaching-review-coverage.md).

The review aimed at one outcome: a beginner-to-intermediate software engineer can learn containers, Docker, and Kubernetes from scratch and reach CKA and CKAD exam readiness.
Main changes:

- Every concept, brief, and debrief now uses a patient teacher's voice: purpose first, terms introduced before use, an action, then what to observe.
- Generic module-wide hints, copied predictions, and templated check messages were replaced with activity-specific ones that name the command to run next.
- Missing prerequisites were added where walkthroughs exposed them, for example cron syntax, dnsPolicy, chmod, loading a local image into kind, and submitting a job in native labs.
- Exam technique and exam-standard commands were added, including a primer covering contexts, imperative commands, `kubectl explain`, vim, and time management, and the etcd backup and restore forms.
- The four practice exams now read like real exam tasks, and their task text has a single source in each exam's `brief.md`.
- Walkthroughs exposed runtime problems, which were reproduced and fixed: resumed clusters reporting ready too early, Docker address pool exhaustion, a Pod subnet overlapping Docker networks, metrics breaking after resume, deadlocked failed labs, and timed exams invalidated when submitted during a rollout.

Valid alternatives were tried deliberately, such as different replica counts, imperative instead of declarative changes, and a different recovery order.
Negative cases were also checked, to confirm that failing messages point at the real cause.

## What remains to establish

These were expert walkthroughs, not sessions with beginner participants.
A beginner usability session should still check whether the explanations are enough without someone filling in gaps.
The independent missions also need broader transfer testing: vary the failure, then see whether a learner can reason through it rather than repeat a recipe.
A score on these practice exams is not evidence of a real exam result.

## Verification

On 2026-09-28, after the course-wide review:

- Ruff, ruff format, mypy, 136 backend tests, frontend lint, formatting, TypeScript, and 5 frontend unit tests passed.
- The structural curriculum audit passed: 96 course units, 12 incidents, and 4 exams.
- The installed browser suites for the learner journey, portability, recovery, saved projects, accessibility, and terminal layout passed.
- A real timed CKAD attempt, submitted while Pods were still rolling, was scored after the fix instead of being invalidated.

The full runtime curriculum audit, which starts every fixture, and the exam browser suite, which needs a separately prepared exam profile, were not rerun.
Grading predicates did not change, apart from the exam grading retry.
Some starter, checkpoint, fixture, and Compose files did change, as recorded in the ledger, and each affected activity passed its walkthrough, but the full runtime audit should be rerun before a release.
