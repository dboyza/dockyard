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

## What remains to establish

The other 105 activities still need comparable learner walkthroughs before claiming a course-wide teaching review.
Priority areas are the Compose transition, storage recovery, GitOps, and native cluster administration, where supplied helpers and infrastructure prerequisites can conceal missing instruction.
The independent missions also need broader transfer testing: vary the failure or requested behavior, then see whether a learner can reason through it without repeating a memorized recipe.
A beginner usability session should check whether the rewritten introduction and terminal guidance are sufficient without an expert filling in gaps.
Automated tests verify navigation, persistence, grading contracts, and regressions; they cannot answer those teaching questions.

## Verification

The installed candidate passed six browser journeys covering real Docker lab work, saved-project continuation, portable progress, recovery, terminal layouts, and accessibility.
Dark and light themes were checked, including widths down to 320 pixels.
The backend suite passed 122 non-integration checks, and five frontend unit checks passed.
Ruff, mypy, frontend lint, formatting, TypeScript, package builds, and the structural curriculum audit passed.
The manual results above are recorded separately from those automated checks.
No grading predicates, reference solutions, runtime lifecycle behavior, or learner progress schema were changed in this review.
Editorial changes preserve existing activity revisions and historical evidence.
Disposable lab resources are cleaned after verification; personal progress and unrelated Docker resources are preserved.

The installer also reported two existing moderate npm dependency advisories in `vitest` and `@vitest/mocker`.
Dependency upgrades were outside this teaching and navigation change.
