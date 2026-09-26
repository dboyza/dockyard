# Release ownership crosses several independent systems

The local source repository, pipeline, registry, Flux source artifact, desired-state directory, and running process each establish a different fact.
A tested image that never reached the registry cannot be pulled by a fresh node.
A pushed image that no Git commit selects does not change the desired release.
A fetched commit with suspended reconciliation does not update a workload.
A successful apply still needs workload health and application behavior checks.

Use the supplied Dispatch checkpoint to connect those boundaries without broadening the deployer's permissions.
Keep source intent, tested image identity, promotion history, and observed recovery consistent.
Document the remaining local compromises: unauthenticated private HTTP, shared practice dependencies, unsigned evidence, and a small single-node capacity budget.

For an independent handoff, describe a release by its source revision and immutable artifact reference, then name the observations that show it is serving correctly.
A useful incident note also records what failed, whether the previous release remained available, how the source was repaired, and which check would catch recurrence.
The note is for your own review; the checker grades runtime behavior and history rather than keywords in prose.
