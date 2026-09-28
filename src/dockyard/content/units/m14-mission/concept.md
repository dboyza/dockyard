## Three tools, three owners

This mission uses all three packaging tools from the module at once, each owning a different part:

- **Kustomize** owns the development environment in namespace `dispatch`.
- **Helm** owns the staging environment in namespace `staging`.
- The **WorkerPool controller** owns development’s worker Deployment.

Keeping each object under one owner matters: if two tools manage the same object, each overwrites the other’s changes.

Right now, all three are broken:
the development overlay has the wrong replica count and environment, the staging release is on a bad revision, and the WorkerPool controller is stopped.
Fix each at its source, then check the running result, not just the files.

There are no step-by-step commands; everything you need is in the three lessons.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
