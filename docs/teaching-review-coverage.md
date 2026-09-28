# Teaching review coverage

This ledger separates completed learner walkthroughs from editorial review and automated runtime audits.
A runtime pass alone is not a teaching-quality result.

| Activity | Learner walkthrough | Editorial review | Findings and observations |
| --- | --- | --- | --- |
| m01-processes | Completed without solutions | Revised | Debrief rewritten without jargon; hints now name concrete commands. |
| m01-lifecycle | Completed without solutions | Revised | Concept introduced writable layer and namespaces without explanation and contradicted the unstarted lab; rewritten around created, running, and exited states. Observed created state and an unchanged ID across restart; passed. |
| m01-signals | Completed without solutions | Revised | Streams, signals, and exit codes now explained in plain terms. Observed the 200 log line and Exited (0); passed. |
| m01-mission | Completed without solutions | Revised | Found the one-shot command from inspect and logs, replaced the container, passed. |
| i01-lifecycle | Completed without solutions | Revised | Required rebuilding an image before docker build was taught; moved after the Dockerfile lesson. Incident template jargon replaced with a plain five-step method. Diagnosed the backgrounded wrapper from Cmd and logs; passed. |
| m02-dockerfile | Completed without solutions | Revised | Layers, tags, and build context now introduced before use. The build warning appears exactly as described; passed. |
| m02-cache | Completed without solutions | Revised | Observed dispatch-1 after both the source edit and rebuild; image and container IDs differed; only the replacement served dispatch-2. Rebuild and replacement commands are now shown with their expected observations. |
| m02-multistage | Completed without solutions | Revised | Built a named verification stage and non-root final stage; observed UID 10001, no /source, and a passing service check. Placeholder build tools replaced with explained Python fragments. |
| m02-mission | Completed without solutions | Revised | Built a two-stage image independently; release and non-root checks passed. Final-state checks do not establish build-stage use or quality of explanation. |
| i02-build-context | Completed without solutions | Revised | Diagnosed staged-context from release.sh and the two VERSION files; passed. Generic incident outcomes and prediction replaced. |
| m03-ports | Completed without solutions | Revised | Observed listener 8080 versus mapping 8081 and an empty reply; corrected mapping passed. Port and loopback diagnostics now name the command to run and the expected mapping. |
| m03-bridges | Completed without solutions | Revised | Observed failed dependency request, then attached both containers with alias; DNS and real peer identity passed. |
| m03-diagnosis | Completed without solutions | Revised | Observed working peer DNS and direct peer HTTP while configured localhost upstream failed; replaced only API with corrected URL, then passed. |
| m03-mission | Completed without solutions | Revised | Passed from source files. A build without the BASE_IMAGE argument fails, and a stale image from an earlier attempt then hid the failure; the brief now reminds learners to supply the argument and read the build result. |
| m04-mounts | Completed without solutions | Revised | Created a job, replaced the container with the same bind mount, and found the same job; passed. |
| m04-permissions | Completed without solutions | Revised | Observed HTTP 503 and root-owned 0700 /data against UID 10001; chown through a maintenance container fixed writes; passed with least-permission check. |
| m04-recovery | Completed without solutions | Revised | Archived the closed database, restored into the stopped target, found the seeded job, and wrote a new job; passed. |
| m04-mission | Completed without solutions | Revised | Stopped the API, copied jobs.db with docker cp, archived, restored into a new labeled volume, replaced the API, and passed. The lesson's docker cp section supplied the missing step. |
| i04-volume-mode | Completed without solutions | Revised | File permission bits were never taught; the incident now explains ls -ln and chmod u+w. Observed readonly database error and -r-------- file; passed. |
| m05-services | Completed without solutions | Revised | Wrote compose.yaml from the lesson fragments; a fresh job completed and passed. The API can be briefly absent from ps while PostgreSQL initializes, which the lesson warns about. |
| m05-readiness | Completed without solutions | Revised | The starter was machine-generated YAML with unexplained anchors and an unused block that already contained the answer; replaced with plain YAML. Missing-health-check failures reported an unrelated worker message; all Compose diagnostics are now specific. Passed after adding the three taught health checks. |
| m05-scaling | Completed without solutions | Revised | Scaled to two workers, observed completed jobs, ran the inspect profile, and restored a pg_dump into a separate database with all four jobs present. |
| m05-mission | Completed without solutions | Revised | Starter is an empty services map. Wrote the full project independently with health checks and two workers; passed. |
| i03-worker-database | Completed without solutions | Revised | Worker logs show only dependency_retry without naming the database; hint now directs learners to compare DB_ settings. Passed. |
| m06-registry | Completed without solutions | Revised | Lesson never showed how to find or run by a digest; now does. RepoDigests held two entries, confirming the need to choose this registry's. Passed. |
| m06-artifacts | Completed without solutions | Revised | Platform and layer-secret explanations rewritten for beginners; passed with .dockerignore. |
| m06-limits | Completed without solutions | Revised | Capabilities and cgroups explained plainly; cgroup values match the lesson; passed. Compose equivalents added because the capstone needs them. |
| m06-mission | Completed without solutions | Revised | Capstone required Compose restriction keys never taught; now taught in m06-limits. Completed with plain SQL backup method from m05; all checks passed. |
| m07-reconciliation | Completed without solutions | Revised | Output matched the lesson: 0/0, rollout, and a replacement Pod with a new UID; passed. Walkthrough exposed a resume bug where a resumed cluster reported ready while every Pod was Unknown; fixed in the runtime. |
| m07-inspection | Completed without solutions | Revised | Rewritten from expert shorthand; now teaches -A, --show-labels, -o yaml, custom-columns, explain, and EndpointSlices. Empty EndpointSlice filled after the selector fix; passed. |
| m07-declarative | Completed without solutions | Revised | Now teaches context switching, server dry runs, diff, and generating YAML with --dry-run=client. Every shown command produced the described output; passed. |
| m07-mission | Completed without solutions | Revised | Fixed replicas and selector independently; passed after waiting for the rollout. |
| m08-workloads | Completed without solutions | Revised | Added a controller comparison, kubectl scale, and generation commands. The new port-forward example first used $DOCKYARD_PORT, which the kind node already publishes, so it failed silently; now uses a free port and was verified to complete a job. Passed. |
| m08-patterns | Completed without solutions | Revised | Observed Init:Error and the configure log exactly as described; fixed init command and shared mount; passed. Verification commands now use deployment/worker to avoid picking a terminating Pod. |
| m08-jobs | Completed without solutions | Revised | Cron syntax was never taught although the lab and CKAD practice exam depend on it; added a cron guide and the psql command to see the maintenance row. Passed. |
| m08-mission | Completed without solutions | Revised | Fixed workers, agent, and CronJob independently; proof Job completed; passed. |
| m09-configmaps | Pending | Pending |  |
| m09-secrets | Pending | Pending |  |
| m09-identities | Pending | Pending |  |
| m09-mission | Pending | Pending |  |
| m10-services | Pending | Pending |  |
| m10-ingress | Pending | Pending |  |
| m10-gateway | Pending | Pending |  |
| m10-mission | Pending | Pending |  |
| i06-service-selector | Pending | Pending |  |
| m11-claims | Pending | Pending |  |
| m11-statefulsets | Pending | Pending |  |
| m11-backup | Pending | Pending |  |
| m11-mission | Pending | Pending |  |
| i08-pending-claim | Pending | Pending |  |
| m12-probes | Pending | Pending |  |
| m12-rollouts | Pending | Pending |  |
| m12-strategies | Pending | Pending |  |
| m12-mission | Pending | Pending |  |
| i05-readiness-port | Pending | Pending |  |
| exam-ckad-a | Pending | Pending |  |
| m13-resources | Pending | Pending |  |
| m13-placement | Pending | Pending |  |
| m13-autoscaling | Pending | Pending |  |
| m13-mission | Pending | Pending |  |
| i10-worker-memory | Pending | Pending |  |
| m14-kustomize | Pending | Pending |  |
| m14-helm | Pending | Pending |  |
| m14-operators | Pending | Pending |  |
| m14-mission | Pending | Pending |  |
| m15-observation | Pending | Pending |  |
| m15-alerts | Pending | Pending |  |
| m15-slo | Pending | Pending |  |
| m15-mission | Pending | Pending |  |
| m16-pipeline | Pending | Pending |  |
| m16-gitops | Pending | Pending |  |
| m16-promotion | Pending | Pending |  |
| m16-mission | Pending | Pending |  |
| i07-registry-identity | Pending | Pending |  |
| m17-rbac | Completed in initial review | Revised in initial review | See teaching-review.md. |
| m17-network | Pending | Pending |  |
| m17-contexts | Pending | Pending |  |
| m17-mission | Pending | Pending |  |
| i09-egress-regression | Pending | Pending |  |
| m18-images | Pending | Pending |  |
| m18-rotation | Pending | Pending |  |
| m18-recovery | Pending | Pending |  |
| m18-mission | Pending | Pending |  |
| exam-ckad-b | Pending | Pending |  |
| m19-runtime | Pending | Pending |  |
| m19-kubelet | Pending | Pending |  |
| m19-control-plane | Pending | Pending |  |
| m19-mission | Pending | Pending |  |
| m20-init | Pending | Pending |  |
| m20-join | Pending | Pending |  |
| m20-ha | Pending | Pending |  |
| m20-mission | Pending | Pending |  |
| m21-drain | Pending | Pending |  |
| m21-upgrade | Pending | Pending |  |
| m21-certificates | Pending | Pending |  |
| m21-mission | Pending | Pending |  |
| m22-packets | Pending | Pending |  |
| m22-dns | Pending | Pending |  |
| m22-storage | Pending | Pending |  |
| m22-mission | Pending | Pending |  |
| m23-etcd | Pending | Pending |  |
| m23-static-pods | Pending | Pending |  |
| m23-api | Pending | Pending |  |
| m23-mission | Pending | Pending |  |
| i12-deleted-state | Pending | Pending |  |
| i11-kubelet-config | Pending | Pending |  |
| m24-triage | Pending | Pending |  |
| m24-decisions | Pending | Pending |  |
| m24-handoff | Pending | Pending |  |
| m24-mission | Pending | Pending |  |
| exam-cka-a | Pending | Pending |  |
| exam-cka-b | Pending | Pending |  |
