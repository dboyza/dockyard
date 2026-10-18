## Reviewing your attempt

Open each task in the results to see what Dockyard checked and what it found.
A task can earn part of its marks when some of its checks pass.

Common gaps in this exam:

- a Localhost profile, seccomp or AppArmor, must exist on every node a Pod might be scheduled to;
- a RuntimeClass handler must match containerd's configuration, and its node selector must match a labeled node;
- containment that deletes the Pod destroys the evidence, and isolation without revoking access leaves the credentials usable;
- a configuration change does not clean a Pod that was already changed; replacing the Pods does;
- `kubectl apply` never deletes objects you removed from a file.

For each task you missed, work through the lesson it links to, then try a fresh attempt without help.
