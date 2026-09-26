## Incident briefing

The release wrapper reports success, then the container exits with status zero.
Clients cannot reach Dispatch.
A new launch wrapper was introduced immediately before the failure.
Restore the long-running service without treating a successful wrapper exit as evidence of availability.
Keep the assigned container identity, loopback endpoint, and owned-resource label.

## Evidence discipline

State the user-visible failure, collect a discriminating observation, and make a bounded repair.
Use the preceding teaching labs and reference desk when needed.
Record the cause, repair, verification, and remaining risk in your observations.
Hints and reference reveal remain available but record supported practice.

The wrapper is part of the supplied image; rebuild that image after editing it and replace the stopped container.
