# Separate the lifetimes

Explain which identities changed when the database Pod was replaced and which remained stable.
Trace the database data directory to its Pod volume, PersistentVolumeClaim, PersistentVolume, and node-local backing directory.
Compare StatefulSet claim retention with the PV reclaim policy; they govern different deletion events.

A successful restore needs readable application records on an independent destination, not merely a backup file or a zero exit status.
Describe the loss boundary of this local lab: deleting the entire kind cluster removes its node-local storage.
For production, consider independent failure domains, off-cluster backups, recovery point and recovery time objectives, and regularly rehearsed restores.
