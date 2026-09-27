# Debrief: Let a controller maintain the application

Changing the desired replica count gave the Deployment controller a target that persists beyond an individual Pod.
Deleting a managed Pod exercises replacement, while deleting its controller removes the owner responsible for maintaining that target.

## Explain your result

Explain why two running Pods without the expected owner references would not demonstrate reconciliation of this Deployment.

## Transfer beyond this lab

Both replicas can share one node here, so replica count alone does not establish availability across independent failure domains.
