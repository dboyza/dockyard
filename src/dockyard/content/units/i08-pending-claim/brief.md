# Incident report

The archive rollout has no running consumer and its new PersistentVolumeClaim remains Pending.
The established API and database continue to work.
Find the dependency between consumer placement and local provisioning.

Retain the original `archive` claim, its `standard` StorageClass, and WaitForFirstConsumer behavior.
Run one `archiver` replica with that claim mounted at `/archive` on an eligible node.
Keep the original Dispatch namespace, database claim, and stored job.
A fresh file must be writable through the archiver mount and readable by a separate consumer of the same claim.
Do not substitute an emptyDir or a host directory directly in the Pod.

Describe the event that made you investigate scheduling instead of restarting the provisioner.
Use the debrief as a self-review rubric.
