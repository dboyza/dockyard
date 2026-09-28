## Upgrade the cluster from 1.34 to 1.35

Upgrade this cluster in place from 1.34.12 to 1.35.8, following the order in Understand: control plane first, then the worker.

- Stage the packages with `python -m dockyard.native stage-upgrade`.
- Both kubelets and the control-plane components must reach 1.35.8.
- Both nodes must end Ready and uncordoned.
- Keep the original namespace, Node objects, marker, and stored data, and complete a new job afterwards.

In your notes, describe when the API was unavailable and when the database was offline, and why.
