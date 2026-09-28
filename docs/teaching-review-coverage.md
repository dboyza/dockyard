# Teaching review coverage

This ledger separates completed learner walkthroughs from editorial review and automated runtime audits.
A runtime pass alone is not a teaching-quality result.

| Activity | Learner walkthrough | Editorial review | Findings and observations |
| --- | --- | --- | --- |
| m01-processes | Completed in initial review | Revised in initial review | See teaching-review.md. |
| m01-lifecycle | Completed in initial review | Revised in initial review | See teaching-review.md. |
| m01-signals | Completed in initial review | Revised in initial review | See teaching-review.md. |
| m01-mission | Completed in initial review | Revised in initial review | See teaching-review.md. |
| i01-lifecycle | Pending | Pending |  |
| m02-dockerfile | Completed in initial review | Revised in initial review | See teaching-review.md. |
| m02-cache | Completed without solutions | Revised | Observed dispatch-1 after both the source edit and rebuild; image and container IDs differed; only the replacement served dispatch-2. Rebuild and replacement commands are now shown with their expected observations. |
| m02-multistage | Completed without solutions | Revised | Built a named verification stage and non-root final stage; observed UID 10001, no /source, and a passing service check. Placeholder build tools replaced with explained Python fragments. |
| m02-mission | Completed without solutions | Revised | Built a two-stage image independently; release and non-root checks passed. Final-state checks do not establish build-stage use or quality of explanation. |
| i02-build-context | Pending | Pending |  |
| m03-ports | Completed without solutions | Revised | Observed listener 8080 versus mapping 8081 and an empty reply; corrected mapping passed. Port and loopback diagnostics now name the command to run and the expected mapping. |
| m03-bridges | Completed without solutions | Revised | Observed failed dependency request, then attached both containers with alias; DNS and real peer identity passed. |
| m03-diagnosis | Completed without solutions | Revised | Observed working peer DNS and direct peer HTTP while configured localhost upstream failed; replaced only API with corrected URL, then passed. |
| m03-mission | Completed without solutions | Revised | Passed from source files. A build without the BASE_IMAGE argument fails, and a stale image from an earlier attempt then hid the failure; the brief now reminds learners to supply the argument and read the build result. |
| m04-mounts | Completed without solutions | Revised | Created a job, replaced the container with the same bind mount, and found the same job; passed. |
| m04-permissions | Completed without solutions | Revised | Observed HTTP 503 and root-owned 0700 /data against UID 10001; chown through a maintenance container fixed writes; passed with least-permission check. |
| m04-recovery | Completed without solutions | Revised | Archived the closed database, restored into the stopped target, found the seeded job, and wrote a new job; passed. |
| m04-mission | Completed without solutions | Revised | Stopped the API, copied jobs.db with docker cp, archived, restored into a new labeled volume, replaced the API, and passed. The lesson's docker cp section supplied the missing step. |
| i04-volume-mode | Pending | Pending |  |
| m05-services | Completed without solutions | Revised | Wrote compose.yaml from the lesson fragments; a fresh job completed and passed. The API can be briefly absent from ps while PostgreSQL initializes, which the lesson warns about. |
| m05-readiness | Completed without solutions | Revised | The starter was machine-generated YAML with unexplained anchors and an unused block that already contained the answer; replaced with plain YAML. Missing-health-check failures reported an unrelated worker message; all Compose diagnostics are now specific. Passed after adding the three taught health checks. |
| m05-scaling | Completed without solutions | Revised | Scaled to two workers, observed completed jobs, ran the inspect profile, and restored a pg_dump into a separate database with all four jobs present. |
| m05-mission | Completed without solutions | Revised | Starter is an empty services map. Wrote the full project independently with health checks and two workers; passed. |
| i03-worker-database | Pending | Pending |  |
| m06-registry | Pending | Pending |  |
| m06-artifacts | Pending | Pending |  |
| m06-limits | Pending | Pending |  |
| m06-mission | Pending | Pending |  |
| m07-reconciliation | Completed in initial review | Revised in initial review | See teaching-review.md. |
| m07-inspection | Pending | Pending |  |
| m07-declarative | Pending | Pending |  |
| m07-mission | Pending | Pending |  |
| m08-workloads | Pending | Pending |  |
| m08-patterns | Pending | Pending |  |
| m08-jobs | Pending | Pending |  |
| m08-mission | Pending | Pending |  |
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
