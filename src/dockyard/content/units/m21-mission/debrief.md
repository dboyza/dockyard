# Debrief: Execute and hand off an in-place maintenance window

The maintenance window upgrades the existing cluster while preserving original namespace and node identities and the pre-maintenance database marker.
The fresh application transaction checks useful service after the version transition rather than assuming version strings imply recovery.

## Explain your result

Document the order of maintenance, the observation that permitted each next step, and the condition that would have required stopping.

## Transfer beyond this lab

A successful local rehearsal is evidence for the mechanism; production timing and disruption risk depend on workload placement and spare capacity.
