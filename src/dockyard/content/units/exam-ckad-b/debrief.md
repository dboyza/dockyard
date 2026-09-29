## Reviewing your attempt

Open each task in the results to see what Dockyard checked and what it found.
A task can earn part of its marks when some of its checks pass.

Common gaps in this exam:

- a digest is only pinned if the Pods actually run `REGISTRY/dispatch@sha256:...`, not just a tag;
- a Kustomize overlay only counts once it is applied and the running Pods use the generated ConfigMap;
- a claim that still exists is not the same as a file restored into it byte for byte;
- two Services can both "work" while sending traffic to the wrong Pods, so check each one's endpoints.

For each task you missed, work through the lesson it links to, then try a fresh attempt without help.
