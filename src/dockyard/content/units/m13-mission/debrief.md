# Debrief: Keep Dispatch available through worker maintenance

The maintenance mission combines placement, available replicas, and disruption policy rather than treating a drain command as the whole operation.
A valid disruption budget can deliberately prevent progress when the remaining replicas cannot satisfy the availability requirement.

## Explain your result

Which evidence justified eviction, and which observation would require adding capacity or repairing a replica before continuing?

## Transfer beyond this lab

A disruption budget governs voluntary disruptions; it does not prevent a node from failing or create spare capacity.
