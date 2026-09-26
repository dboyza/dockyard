## Incident briefing

The API and its readiness check work, and newly submitted jobs appear in the queue, but background results never finish.
A worker-specific configuration overlay was deployed immediately before the symptom; the API, queue, and database processes stayed healthy.
Restore two interchangeable workers while preserving the current PostgreSQL volume, private dependency network, and API endpoint.
Prove a new job completes through a real worker and persists in the database.

## Evidence discipline

State the user-visible failure, collect a discriminating observation, and make a bounded repair.
Use the preceding teaching labs and reference desk when needed.
Record the cause, repair, verification, and remaining risk in your observations.
Hints and reference reveal remain available but record supported practice.
