Upgrade this existing 1.34.12 cluster to 1.35.8 in place.
Both kubelets and the three Kubernetes control-plane components must reach the target version, and both nodes must return Ready and schedulable.
Preserve the original namespace, Node objects, maintenance sentinel, and stored database row.
Complete a fresh Dispatch job after maintenance.
Use the staged verified packages, follow the control-plane-first sequence, and explain the API and database downtime boundaries in your notes.
