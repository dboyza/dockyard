## Reviewing your attempt

Open each task in the results to see what Dockyard checked and what it found.
A task can earn part of its marks when some of its checks pass.

Common gaps in this exam:

- a snapshot file is only useful if `etcdutl snapshot status` can read it, and a backup is not proven until you have practised a restore;
- RBAC is only right when the allowed actions succeed *and* the forbidden ones are refused;
- a DaemonSet needs tolerations for every tainted node, and in a restricted namespace its Pods also need a matching security context;
- a StatefulSet Pod stuck on an old template may need deleting before it picks up your change.

For each task you missed, work through the lesson it links to, then try a fresh attempt without help.
