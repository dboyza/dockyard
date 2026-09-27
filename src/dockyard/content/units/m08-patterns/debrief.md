# Debrief: Coordinate containers inside a Pod

The init container establishes shared configuration before the main containers start, and the sidecar observes files in the same Pod volume.
Sharing that volume connects the containers without making their files durable beyond the volume lifetime.

## Explain your result

Identify the order constraint enforced by the init container and explain why an unrelated file in another Pod would not prove this coordination.

## Transfer beyond this lab

Use a separate durable storage design when a process must retain this state after its Pod is replaced.
