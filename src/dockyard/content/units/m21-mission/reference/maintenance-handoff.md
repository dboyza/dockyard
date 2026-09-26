# Maintenance handoff

The original 1.34.12 cluster was upgraded in place to 1.35.8.
Kubeadm was installed first on each node; the primary used upgrade apply and the worker used upgrade node.
Each kubelet was updated during a drain and returned to scheduling afterward.
The single control plane incurred API downtime, and the worker-local database incurred application downtime during worker maintenance.
The original namespace, Node objects, marker, and SQL sentinel remained intact, and a new Dispatch transaction completed.
The lab identity checks are not a substitute for a tested production backup and restore plan.
The physical host, API endpoint, and local database storage remain single failure points.
