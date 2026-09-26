# Hand off a recoverable local delivery workflow

A publication gate has been bypassed and both release targets are suspended.
Repair the pipeline and source reconciliation, publish a tested release, and establish current healthy controller revisions.
Demonstrate drift repair, promotion of the same tested dispatch-3 digest, a real failed candidate pull, and recovery through a new Git revert commit.
The supplied helpers are available for inspection and use, but diagnose each boundary yourself before running them.
Keep the deployer scoped to Dispatch Deployments and preserve the independent database credential.
Write DELIVERY-NOTES.md explaining the chain of evidence, the failed candidate's actual user impact, and how a future operator would repeat or reverse a release.
