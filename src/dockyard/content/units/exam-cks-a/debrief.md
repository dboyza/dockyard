## Reviewing your attempt

Open each task in the results to see what Dockyard checked and what it found.
A task can earn part of its marks when some of its checks pass.

Common gaps in this exam:

- a changed kubelet configuration does nothing until the kubelet restarts, and the live configuration is what counts;
- removing an anonymous binding leaves anonymous requests reaching RBAC; restricting anonymous authentication is the second half;
- a static Pod reads a new file only through a matching `hostPath` volume and mount;
- encryption at rest covers only Secrets written after it is enabled, so existing ones must be rewritten;
- an AppArmor profile must be loaded on every node a Pod might use, and installed for boot;
- an egress policy without a DNS rule breaks every Service name lookup.

For each task you missed, work through the lesson it links to, then try a fresh attempt without help.
