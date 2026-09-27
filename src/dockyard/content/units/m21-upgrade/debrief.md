# Debrief: Upgrade the actual control plane and kubelets in place

The existing API, control-plane images, and kubelets move through the supported adjacent-version upgrade while original identities and data remain.
Recreating a new cluster at the target version would not establish an in-place upgrade or continuity of the old cluster.

## Explain your result

Compare the API version, static component images, and every kubelet version, then explain why a new persisted job is still needed after they agree.

## Transfer beyond this lab

Plan maintenance around supported version skew, backups, disruption constraints, and a recovery strategy suited to the actual cluster topology.
