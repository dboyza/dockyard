# Migrate and apply the manifest

The cluster currently runs one Dispatch replica.
Your workspace contains a desired two-replica Deployment written with the removed `extensions/v1beta1` API version.

1. Confirm the private context and namespace.
2. Attempt a server dry run and explain the unsupported API error.
3. Migrate the manifest to the supported Deployment API and keep its explicit selector matching the Pod labels.
4. Inspect the diff, apply, and wait for the two-replica rollout.
5. Add a `CHANGE.md` note describing why changing only the namespace would not repair this error.

The automated check validates the live result and the source manifest's supported API version.
Your explanation is a self-review artifact, not automatically scored prose.
