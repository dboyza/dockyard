# Using Dockyard

See [platform setup](platforms.md) for macOS, Linux, and Windows through WSL 2.

## Choose your starting point

Launch `./dockyard` from the repository after installation.
The workbench listens on loopback and opens a browser with a short-lived, single-use sign-in.
The address fragment disappears after authentication.
An unrelated browser cannot operate the lab API without its session cookie.

If you already know some Docker or Kubernetes, open **Your course → Find your starting point**.
Try a mission to see which topics need practice; every lesson remains available.
Your course remains freely browsable, with searchable explanations and supplied checkpoints for later modules.
Reference desk contains supporting primers and a searchable glossary.

## Meet Dispatch

Dispatch is the supplied application you will learn to run.
It grows from an API that answers health requests into a background job service with a queue, worker, and database.
The worker changes submitted text to uppercase and records a result; it is deliberately small so you can focus on operating the system.
You do not need to write its Python code.
The Overview page explains the project before you start.

The sidebar has five main destinations: Overview, Your course, Practice, Your progress, and Lab manager.
Placement lives within Your course; troubleshooting and exams live within Practice; reviews and saved projects live within Your progress.
Reference desk and Settings and data stay at the bottom of the sidebar.
Find a lesson using the search field at the top of the page, or press `/` from anywhere to jump to it and Escape to clear it.
The sidebar shows how many labs exist on this computer, so a forgotten cluster is easy to spot.

## Complete a lab

1. Read **Understand** and answer the prediction before inspecting the explanation.
2. Read **Your task** and prepare the owned environment.
3. Select **Open terminal** to open an ordinary terminal in that activity's workspace.
4. Edit files and run commands using your preferred terminal tools.
5. Select **Check work** and start with any item marked Needs attention.
   Open Check details to see the expected and observed values.
6. Write observations and use the debrief to explain why the repair worked.
   Observations save when you click out of the notes box, or with Save observations.
7. Use Previous and Next at the bottom of the lesson to move through the course in order.

Every command block has a copy button in its top corner.

A terminal retains its original lab identity when the browser switches lessons.
Reopen the terminal after Reset or Independent retake so the workspace and attempt agree.
Checks use live behavior and source snapshots; changing files or resources during a check can make its result stale.
A stopped or unavailable environment is reported as blocked rather than as a learner failure.

Hints reveal progressively.
Reference solutions require an explicit reveal and mark the current attempt as supported.
Independent retake backs up the workspace, restores the starter, and begins a new support record while retaining earlier evidence.
Your progress separates guided practice from missions passed without in-app hints or references.
A pass records the lab’s behavior at the time of the check.
It does not grade your explanation, prove retention, or detect help used outside Dockyard.

## Grow the Dispatch project

Passing a mission stores a source checkpoint with its revision, evidence, observations, and support provenance.
Subsequent edits do not modify that archive.
Open **Your progress → Saved projects** to download a checkpoint or a portfolio containing the latest checkpoint from each completed mission.

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

Open **Practice → Troubleshooting** to investigate a broken application in a separate lab.
They preserve the main project's source checkpoints.
Each scenario asks for diagnostic evidence and a repair with a verifiable result.

Open **Practice → Exam practice** for two CKAD-oriented and two CKA-oriented original task sets.
Prepare the environment before starting its 120-minute timer.
The interface shows task points, allowed-reference policy, flags, remaining time, and a saved report with links to the lessons to revisit.
While an attempt is running, the remaining time also appears in the top bar on every other page.
Task weights total 100 and permit partial credit where an assessed task has multiple criteria.

Browser reload does not reset the deadline.
The running workbench grades at expiry even when the browser is closed.
If the workbench process is unavailable at the deadline, or infrastructure prevents reliable grading, the attempt is invalidated without assigning a score.
If Pods are still starting or stopping when you submit, grading waits and checks again for up to about a minute before deciding the environment is too unsettled to score.
Keep the workbench process running during timed practice.
Hints and reference reveals are unavailable during an active timed attempt.
Use Independent retake before starting another timer on an already assessed or supported fixture.
These exercises do not reproduce certification proctoring or estimate a probability of passing an exam.

## Operate your labs

Lab Manager lists the labs that exist on this computer, with Stop all when several are running, and reports Docker health, architecture, host memory, and free disk.
Dockyard permits one active application cluster or native VM lab across its registered profiles.
Switching within one profile stops its previous ready owned cluster.
A cluster in another profile must be stopped or cleaned from that profile before another starts.
A failed environment is stopped like a ready one when another cluster lab starts; its error stays visible for when you return to it.
A lab that is still preparing, checking, stopping, or cleaning must finish first.
Unrelated Docker resources are not stopped to make room.
Every Docker and kind lab uses its own Docker network, and Docker has a limited number of private address ranges.
When none remain, preparing a lab cleans the least recently used stopped lab and tries again, up to eight times.
Its workspace and progress are kept, the lab shows why it was removed, and preparing it again reapplies your files.
Running and failed labs are never reclaimed.

| Action | Effect |
| --- | --- |
| Prepare | Creates missing source and owned runtime prerequisites; preserves existing source. |
| Check | Observes the selected activity's source and actual runtime behavior. |
| Stop | Pauses owned containers or VMs and retains their disks and source. |
| Resume | Restarts the preserved environment and verifies its prior readiness contract. |
| Reset | Backs up the complete workspace and restores the starter environment. |
| Independent retake | Performs a reset and starts a fresh learning-support record. |
| Clean up | Removes verified owned runtime resources, their anonymous volumes, and images named for the lab or pushed to its registry, while preserving source and history. |

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
./dockyard lab status
./dockyard cache status module:1
./dockyard cache prepare track:1
./dockyard cache clean
./dockyard progress export ./my-learning.zip
./dockyard progress import ./my-learning.zip
./dockyard progress import ./my-learning.zip --yes
./dockyard portfolio ./dispatch-portfolio.zip
```

Export destinations must not already exist.
The import command previews by default; `--yes` merges the validated archive.
`lab status` without an activity lists every lab in the profile.
`cache clean` lists the container images Dockyard downloaded; add `--yes` to remove them.
Most commands print a readable summary; add `--json` for scripts.
Use `--data-dir PATH` before the subcommand for a separate profile.
Native VM profiles require short paths because Lima Unix socket paths have a fixed length limit.
The default profile is `~/Library/Application Support/Dockyard` on macOS and `~/.local/share/dockyard` on Linux and WSL.
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

## Remove Dockyard

1. Back up anything you want to keep with `./dockyard progress export dockyard-backup.zip`.
2. Remove every lab's containers, clusters, networks, volumes, images, and VMs with `./dockyard lab clean --all --yes`.
   It only touches resources Dockyard recorded as its own.
3. Remove the container images Dockyard downloaded, such as Python and PostgreSQL, with `./dockyard cache clean --yes`.
   It keeps any image a container still uses and any tag you added yourself.
4. Delete the data folder that `./dockyard doctor` lists as **Data**.
   It holds your progress, notes, lab workspaces, and the tools and VM images Dockyard downloaded for that profile.
5. Delete the Dockyard folder you installed from, which also removes its private `.runtime` and `.tools` folders.

Dockyard never edits your shell configuration, Docker settings, or default kubeconfig, so there is nothing to undo there.
