# Debrief: Recover a CSI volume with incompatible workload placement

The original CSI volume must be attached and mounted by the database on a compatible worker, with its data still intact.
A Bound claim can coexist with an attachment or placement failure, so claim phase alone cannot establish storage use.

## Explain your result

Trace the workload’s selected node, driver registration, attachment, mount, and preserved database row to identify the actual failed boundary.

## Transfer beyond this lab

Production CSI behavior depends on the storage provider’s topology and access modes; the local hostpath driver demonstrates mechanisms rather than remote-storage durability.
