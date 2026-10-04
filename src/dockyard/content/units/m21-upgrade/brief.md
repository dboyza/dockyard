## Upgrade the cluster from 1.36 to 1.37

Upgrade this cluster in place from 1.36.5 to 1.37.1, following the order in Understand: control plane first, then the worker.

- Stage the packages with `python -m dockyard.native stage-upgrade`.
- Both kubelets and the control-plane components must reach 1.37.1.
- Both nodes must end Ready and uncordoned.
- Keep the original namespace, Node objects, marker, and stored data, and complete a new job afterwards.

In your notes, describe when the API was unavailable and when the database was offline, and why.
