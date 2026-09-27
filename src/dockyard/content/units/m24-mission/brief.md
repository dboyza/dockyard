Recover Dispatch while the primary API server and etcd member remain stopped.
Preserve all three voting memberships and original cluster/data identities, repair the private endpoint and application workflow, meet the stated API resource/disruption budgets, and restore least-privilege inventory access.
Prove new API writes and a new completed persistent job.
Deliver `handoff.md` with reproducible observations, bounded repair steps, and remaining availability limitations.

Build the final Dispatch release with `VERSION` set to `dispatch-handoff-v1`, transfer its image into these guests, and roll both the API and worker onto that built artifact.
Verify the running release rather than changing only the workspace file.
