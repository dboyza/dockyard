# Using Dockyard

See [platform setup](platforms.md) for macOS, Linux, and Windows through WSL 2.

## Choose your starting point

Launch `./dockyard` from the repository after installation.
The workbench listens on loopback and opens a browser with a short-lived, single-use sign-in.
The address fragment disappears after authentication.
An unrelated browser cannot operate the lab API without its session cookie.

Start with Practical placement if you have intermediate experience.
Its benchmarks use real lab outcomes to recommend a starting point; a self-rating alone does not mark skills demonstrated.
Your course remains freely browsable, with searchable explanations and supplied checkpoints for later modules.
Reference desk contains supporting primers and a searchable glossary.

## Complete a lab

1. Read **Understand** and answer the prediction before inspecting the explanation.
2. Read **Your task** and prepare the owned environment.
3. Select **Open terminal** to open an ordinary terminal in that activity's workspace.
4. Edit files and run commands using your preferred terminal tools.
5. Select **Check work** and read both passing observations and failed boundaries.
6. Save observations and use the debrief to explain why the repair worked.

A terminal retains its original lab identity when the browser switches lessons.
Reopen the terminal after Reset or Independent retake so the workspace and attempt agree.
Checks use live behavior and source snapshots; changing files or resources during a check can make its result stale.
A stopped or unavailable environment is reported as blocked rather than as a learner failure.

Hints reveal progressively.
Reference solutions require an explicit reveal and mark the current attempt as supported.
Independent retake backs up the workspace, restores the starter, and begins a new support record while retaining earlier evidence.
A passing practice attempt and an independent demonstration are distinct in Skill evidence.

## Grow the Dispatch project

Passing a mission stores a source checkpoint with its revision, evidence, observations, and support provenance.
Subsequent edits do not modify that archive.
Project checkpoints can download an individual checkpoint or a combined portfolio containing the latest checkpoint from each completed mission.

To continue earlier work, expand **Continue in a later mission**, select an unstarted mission, and compare files.
Nothing is selected automatically.
Carry only the files you want to adapt; the remaining files come from the new mission's supplied scaffold.
Earlier application code may not match a later architecture, so review the differences before carrying it forward.
Creating the workspace does not start an environment or run any selected script.
An existing mission workspace is preserved and cannot be replaced through this action.
A supported checkpoint keeps its continuation marked as supported practice until an independent retake.

Checkpoint and portfolio manifests list source exclusions and credential-bearing document transformations.
Runtime databases, backup data, private keys, transient kubeconfigs, and image caches do not belong in the portfolio.
Recovery labs teach database backup and restore separately.

## Practice incidents and timed exams

Incident scenarios use separate workspaces and environments with original faults.
They preserve the main project's source checkpoints.
Each scenario asks for diagnostic evidence and a repair with a verifiable result.

Exam practice contains two CKAD-oriented and two CKA-oriented original task sets.
Prepare the environment before starting its 120-minute timer.
The interface shows task weights, allowed-reference policy, flags, remaining time, and a saved report with remediation links.
Task weights total 100 and permit partial credit where an assessed task has multiple criteria.

Browser reload does not reset the deadline.
The running workbench grades at expiry even when the browser is closed.
If the workbench process is unavailable at the deadline, or infrastructure prevents reliable grading, the attempt is invalidated without assigning a score.
Keep the workbench process running during timed practice.
Hints and reference reveals are unavailable during an active timed attempt.
Use Independent retake before starting another timer on an already assessed or supported fixture.
These exercises do not reproduce certification proctoring or estimate a probability of passing an exam.

## Operate your labs

Lab Manager reports Docker health, architecture, host memory, free disk, and saved environment states.
Dockyard permits one active application cluster or native VM lab across its registered profiles.
Switching within one profile stops its previous ready owned cluster.
A cluster in another profile must be stopped or cleaned from that profile before another starts.
A failed environment requires inspection and Stop or Clean up before switching the budget.
Unrelated Docker resources are not stopped to make room.

| Action | Effect |
| --- | --- |
| Prepare | Creates missing source and owned runtime prerequisites; preserves existing source. |
| Check | Observes the selected activity's source and actual runtime behavior. |
| Stop | Pauses owned containers or VMs and retains their disks and source. |
| Resume | Restarts the preserved environment and verifies its prior readiness contract. |
| Reset | Backs up the complete workspace and restores the starter environment. |
| Independent retake | Performs a reset and starts a fresh learning-support record. |
| Clean up | Removes verified owned runtime resources while preserving source and history. |

Closing a browser does not stop lab resources.
Stop the environment explicitly when you finish a session.
An external terminal has your ordinary host permissions; do not run commands against unrelated projects or real infrastructure.

## Prepare a cache

Select a module, learning track, individual activity, or the full course in Lab Manager.
Inspect cache checks pinned tool hashes, native package hashes, and native-architecture image availability.
Prefetch downloads missing declared dependencies and keeps verified downloads when canceled.
A repeated preparation can resume supported partial downloads.
The private cache has a 40 GiB soft budget; Docker images and build cache remain in Docker Desktop's shared storage.
Dockyard never performs a global prune.

A cached base image is insufficient to guarantee every later build works offline.
The report identifies Python dependency builds that may need package-index access after build-cache eviction, and fresh native bootstrap or upgrades that still need control-plane registry access.
Prepared local labs remain usable without cloud services, subject to their running runtime dependencies.
Changing versions or adding dependencies can introduce new downloads.

## Keep a portable history

Settings and data exports progress, assessments, saved exam attempts, observations, mission checkpoints, and portable source drafts.
It excludes live resource ownership and known lab credentials.
Inspect an import before confirming its merge.
The app verifies archive boundaries and hashes, backs up the local database, retains existing notes, and stores imported drafts and conflicting observations in a separate import folder.
It does not overwrite active workspace files or recreate containers and VMs.
Unfinished imported exams are invalidated without a score.
Repeated import of the same archive is idempotent.
Older curriculum evidence stays historical and remains due for reassessment where revisions differ.

## Use the CLI

```sh
./dockyard doctor
./dockyard lab prepare m01-processes
./dockyard lab shell m01-processes
./dockyard lab check m01-processes
./dockyard lab stop m01-processes
./dockyard cache status module:1
./dockyard cache prepare track:1
./dockyard progress export ./my-learning.zip
./dockyard progress import ./my-learning.zip
./dockyard progress import ./my-learning.zip --yes
./dockyard portfolio ./dispatch-portfolio.zip
```

Export destinations must not already exist.
The import command previews by default; `--yes` merges the validated archive.
Use `--data-dir PATH` before the subcommand for a separate profile.
Native VM profiles require short paths because Lima Unix socket paths have a fixed length limit.
The default profile is `~/Library/Application Support/Dockyard`.
The app uses a private tools directory inside an installed profile, and never edits the default kubeconfig.

## Recover from an interrupted operation

Read the diagnostic first and inspect the lab's preserved state.
Retry a canceled download or preparation after connectivity or disk space is restored.
A second tab cannot take over an already running operation on the same lab.
Interrupted ownership is recovered when the next operation obtains its exclusive process lock.
If a required tool or image is missing, use Lab Manager to inspect its cache and prefetch again.
If a port is occupied, preserve the other process and prepare a fresh owned environment after reviewing the diagnostic.

For a suspected defect, retain the activity ID, app version, operation, and visible diagnostic.
Do not attach private runtime data or credentials to a report.
